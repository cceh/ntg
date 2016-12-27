/**
 * Comparison of 2 witnesses
 *
 * @module comparison
 * @author Marcello Perathoner
 */

define (['jquery',
         'jquery-csv',
         'datatables.net',
         'datatables-bs',
         'css!bootstrap-css',
         'css!datatables-bs-css',
         'css!site-css',
         'css!comparison-css'],

function ($) {
    'use strict';

    var module = {};

    var default_table_options = {
        'autoWidth'    : true,
        'deferRender'  : true,
        'info'         : false,
        'lengthChange' : false,
        'ordering'     : true,
        'paging'       : false,
        'scrollX'      : false,
        'searching'    : false,
    };

    function create_child_table (ms1, ms2) {
        return $ (
            '<div class="slider">' +
              '<table cellspacing="0" width="100%" ' +
                'class="comparison-detail table table-bordered table-condensed table-hover">' +
                '<thead>' +
                  '<tr>' +
                    '<th class="passage">Passage</th>' +
                    '<th class="lesart lesart1">Lesart</th>' +
                    '<th class="ms ms1">' + ms1 + '</th>' +
                    '<th class="direction">Dir</th>' +
                    '<th class="ms ms2">' + ms2 + '</th>' +
                    '<th class="lesart lesart2">Lesart</th>' +
                  '</tr>' +
                '</thead>' +
              '</table>' +
            '</div>'
        );
    }

    /**
     * The inverse of the jQuery.param () function.
     *
     * @param s
     *
     * @return array
     */

    function deparam (s) {
        return s.split ('&').reduce (function (params, param) {
            var paramSplit = param.split ('=').map (function (value) {
                return decodeURIComponent (value.replace ('+', ' '));
            });
            params[paramSplit[0]] = paramSplit[1];
            return params;
        }, {});
    }

    function init_table () {
        var $table = $ ('table.comparison');
        var $tbody = $ ('tbody', $table);

        var table = $table.DataTable ($.extend ({}, default_table_options, { // eslint-disable-line new-cap
            'columns' : [
                {
                    'class'          : 'details-control',
                    'orderable'      : false,
                    'data'           : null,
                    'defaultContent' : '',
                },
                {
                    'data'  : 'chapter',
                    'class' : 'chapter',
                },
                { /* ms1 */
                    'data'      : null,
                    'class'     : 'ms ms1',
                    'render'    : function () { return module.ms1.hs; },
                    'orderable' : false,
                },
                { /* dir */
                    'data'   : null,
                    'class'  : 'direction',
                    'render' : function (r /* , type, full, meta */) {
                        if (r.older > r.newer) {
                            return '-->';
                        }
                        if (r.older === r.newer) {
                            return '';
                        }
                        return '<--';
                    },
                },
                { /* ms2 */
                    'data'      : null,
                    'class'     : 'ms ms2',
                    'render'    : function () { return module.ms2.hs; },
                    'orderable' : false,
                },
                { 'data': 'rank' },
                { /* affinity */
                    'data'   : null,
                    'render' : function (r /* , type, full, meta */) {
                        return Math.round (r.affinity * 100000) / 1000;
                    },
                },
                { 'data': 'equal' },
                { 'data': 'common' },
                { 'data': 'newer' },
                { 'data': 'older' },
                { 'data': 'unclear' },
                { /* norel */
                    'data'   : null,
                    'render' : function (r /* , type, full, meta */) {
                        return (r.common - r.equal - r.older - r.newer - r.unclear);
                    },
                },
            ],
            'order'      : [[1, 'asc']],
            'createdRow' : function (row, data, dummy_index) {
                $ (row).attr ('data-chapter', data.chapter);
            },
        }));

        $tbody.on ('click', 'td.details-control', function () {
            var $tr = $ (this).closest ('tr');
            var row = table.row ($tr);

            if (row.child.isShown ()) {
                $ ('div.slider', row.child ()).slideUp (function () {
                    row.child.hide ();
                    $tr.removeClass ('shown');
                });
            } else {
                if ($tr.hasClass ('csv-loaded')) {
                    $tr.addClass ('shown');
                    row.child.show ();
                    $ ('div.slider', row.child ()).slideDown ();
                    return;
                }
                var $childTable = create_child_table (module.ms1.hs, module.ms2.hs);
                row.child ($childTable, 'no-padding').show ();
                $tr.addClass ('shown');

                var params2 = {
                    'ms1'     : module.ms1.hsnr,
                    'ms2'     : module.ms2.hsnr,
                    'chapter' : $tr.attr ('data-chapter'),
                };

                $.get ('comparison-detail.csv?' + $.param (params2), function (detail_csv) {
                    $tr.addClass ('csv-loaded');
                    $childTable.find ('table').dataTable (
                        $.extend ({}, default_table_options, {
                            'data'    : $.csv.toObjects (detail_csv),
                            'columns' : [
                                {
                                    'data' : function (r, type /* , val, meta */) {
                                        if (type === 'sort') {
                                            return 1000000 + Number (r.pass_id);
                                        }
                                        return r.pass_hr;
                                    },
                                    'class' : 'passage',
                                },
                                {
                                    'data'  : 'lesart1',
                                    'class' : 'lesart lesart1',
                                },
                                {
                                    'data'  : 'var1',
                                    'class' : 'ms ms1',
                                },
                                {
                                    'data'  : 'direction',
                                    'class' : 'direction',
                                },
                                {
                                    'data'  : 'var2',
                                    'class' : 'ms ms2',
                                },
                                {
                                    'data'  : 'lesart2',
                                    'class' : 'lesart lesart2',
                                },
                            ],
                            'order' : [[0, 'asc']],
                        })
                    );
                    $ ('div.slider', row.child ()).slideDown ();
                });
            }
        });
    }

    function load_table () {
        var $table = $ ('table.comparison');

        var params = {
            'ms1' : module.ms1.hsnr,
            'ms2' : module.ms2.hsnr,
        };

        $.get ('comparison.csv?' + $.param (params), function (comparison_csv) {
            var table = $table.DataTable (); // eslint-disable-line new-cap
            table.clear ().rows.add ($.csv.toObjects (comparison_csv)).draw ();
        });
    }

    function fix (s) {
        var re = /^\d+$/;
        s = s + '';
        if (re.test (s) && s.length < 6) {
            return s + '.'
        }
        return s;
    }

    function init_nav () {
        // User hit 'Go'
        $ ('form.manuscripts-selector').on ('submit', function (event) {
            var q = $ (event.currentTarget).serializeArray ();
            q[0].value = fix (q[0].value);
            q[1].value = fix (q[1].value);
            window.location.hash = '#' + $.param (q);
            event.preventDefault ();
        });

        // From above or user hit back-button, etc.
        $ (window).on ('hashchange', function () {
            $ (document).trigger ('ntg.comparison.changed');
        });

        $ (document).on ('ntg.comparison.changed', function (/* event */) {
            var hash = window.location.hash.substring (1);
            if (hash) {
                var p = deparam (hash);

                var p1 = $.getJSON ('manuscript.json/' + p.ms1, function (json) {
                    module.ms1 = json;
                });
                var p2 = $.getJSON ('manuscript.json/' + p.ms2, function (json) {
                    module.ms2 = json;
                });

                $.when (p1, p2).done (function () {
                    var $form = $ ('form.manuscripts-selector');
                    $ ('input[name="ms1"]', $form).val (p.ms1);
                    $ ('input[name="ms2"]', $form).val (p.ms2);

                    var $h1 = $ ('h1');
                    $ ('span.ms1', $h1).text (p.ms1);
                    $ ('span.ms2', $h1).text (p.ms2);

                    $ ('div.panel-comparison-header').text ($h1.text ());
                    $ ('title').text ($h1.text ());

                    load_table ();
                });
            }
        });
    }

    /**
     * Initialize the module.
     *
     * @function init
     */
    function init () {
        init_nav ();
        init_table ();
        $ (document).trigger ('ntg.comparison.changed');
    }

    module.init = init;
    return module;
});
