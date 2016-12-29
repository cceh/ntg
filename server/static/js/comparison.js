/**
 * Comparison of 2 witnesses.  This module shows a table with a global
 * comparison of two witnesses: in how many passages do they differ, how many
 * are older / younger? There is also a drill-down table for each chapter with
 * more detail about the differing passages.
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

    /**
     * Return a skeleton for a drill-down table.
     *
     * @function create_child_table
     *
     * @param ms1 {string} Name of the first manuscript to compare.
     * @param ms2 {string} Name of the second manuscript to compare.
     *
     * @return {jQuery} The HTML skeleton.
     */

    function create_child_table (ms1, ms2) {
        return $ (
            '<tr class="no-padding">' +
              '<td class="no-padding"></td>' +
              '<td class="no-padding" colspan="12">' +
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
                '</div>' +
              '</td>' +
            '</tr>'
        );
    }

    /**
     * The inverse of the jQuery.param () function.
     *
     * @function deparam
     *
     * @param s {string} A string in the form "p=1&q=2"
     *
     * @return {Object} { p : 1, q : 2 }
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

    /**
     * Initialize the table structure.  This has to be done only once.  On
     * navigation we only replace the table data.
     *
     * @function init_table
     */

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
                {
                    'data'  : 'direction',
                    'class' : 'direction',
                },
                { /* ms2 */
                    'data'      : null,
                    'class'     : 'ms ms2',
                    'render'    : function () { return module.ms2.hs; },
                    'orderable' : false,
                },
                {
                    'data'  : 'rank',
                    'class' : 'equal',
                },
                { /* affinity */
                    'data'   : null,
                    'class'  : 'equal',
                    'render' : function (r /* , type, full, meta */) {
                        return Math.round (r.affinity * 100000) / 1000;
                    },
                },
                {
                    'data'  : 'equal',
                    'class' : 'equal',
                },
                {
                    'data'  : 'common',
                    'class' : 'common',
                },
                {
                    'data'  : 'newer',
                    'class' : 'newer',
                },
                {
                    'data'  : 'older',
                    'class' : 'older',
                },
                {
                    'data'  : 'unclear',
                    'class' : 'unclear',
                },
                { /* norel */
                    'data'   : null,
                    'class'  : 'norel',
                    'render' : function (r /* , type, full, meta */) {
                        return (r.common - r.equal - r.older - r.newer - r.unclear);
                    },
                },
            ],
            'order'      : [[1, 'asc']],
            'createdRow' : function (row, data, dummy_index) {
                var $row = $ (row);
                $row.attr ('data-chapter', data.chapter);
                $row.toggleClass ('older', data.older > data.newer);
                $row.toggleClass ('newer', data.older < data.newer);
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

                $.get ('comparison-detail.csv?' + $.param (params2), function (csv) {
                    $tr.addClass ('csv-loaded');
                    $childTable.find ('table').dataTable (
                        $.extend ({}, default_table_options, {
                            'data'    : $.csv.toObjects (csv),
                            'columns' : [
                                {
                                    'data' : function (r, type /* , val, meta */) {
                                        if (type === 'sort') {
                                            return 1000000 + Number (r.pass_id);
                                        }
                                        return '<a href="coherence#' + r.pass_id + '">' + r.pass_hr + '</a>';
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
                            'order'      : [[0, 'asc']],
                            'createdRow' : function (r, data /* , index */) {
                                var $row = $ (r);
                                $row.toggleClass ('older', data.older > data.newer);
                                $row.toggleClass ('newer', data.older < data.newer);
                            },
                        })
                    );
                    $ ('div.slider', row.child ()).slideDown ();
                });
            }
        });
    }

    /**
     * Called after navigation.  Redraws the whole page.
     *
     * @function on_navigation
     */

    function on_navigation () {
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

                var caption = $ ('span.caption', $h1).text ();
                $ ('div.panel-comparison-header span.caption').text (caption);
                $ ('title').text (caption);

                // reload table
                var url = 'comparison.csv?' + $.param ({
                    'ms1' : module.ms1.hsnr,
                    'ms2' : module.ms2.hsnr,
                });
                $ ('a.btn-csv-download').attr ('href', url);

                $.get (url, function (csv) {
                    var table = $ ('table.comparison').DataTable (); // eslint-disable-line new-cap
                    table.clear ().rows.add ($.csv.toObjects (csv)).draw ();
                });
            });
        }
    }

    /**
     * Init the navigation elements.  Also listen for hashtag events.
     *
     * @function init_nav
     */

    function init_nav () {
        function fix (s) {
            var re = /^\d+$/;
            s += '';
            if (re.test (s) && s.length < 6) {
                return s + '.';
            }
            return s;
        }

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

        // Hook
        $ (document).on ('ntg.comparison.changed', function (/* event */) {
            on_navigation ();
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
        on_navigation ();
    }

    module.init = init;
    return module;
});
