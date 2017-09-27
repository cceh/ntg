'use strict';

/**
 * Comparison of 2 witnesses.  This module shows a table with a global
 * comparison of two witnesses: in how many passages do they differ, how many
 * are older / younger? There is also a drill-down table for each range with
 * more detail about the differing passages.
 *
 * @module comparison
 * @author Marcello Perathoner
 */

define(['jquery', 'd3', 'tools', 'datatables.net', 'datatables.net-bs', 'datatables.net-buttons', 'datatables.net-buttons-bs', 'datatables.net-buttons-html5', 'datatables.net-buttons-print', 'css!bootstrap-css', 'css!datatables-bs-css', 'css!datatables-buttons-bs-css', 'css!site-css', 'css!comparison-css'], function ($, d3, tools) {
    var module = {};

    var default_table_options = {
        'autoWidth': true,
        'deferRender': true,
        'info': false,
        'lengthChange': false,
        'ordering': true,
        'paging': false,
        'scrollX': false,
        'searching': false
    };

    var default_buttons = [{
        'extend': 'copy',
        'className': 'btn btn-primary btn-comparison-copy',
        'exportOptions': { 'columns': '.exportable' }
    }, {
        'extend': 'csv',
        'className': 'btn btn-primary btn-comparison-csv',
        'exportOptions': { 'columns': '.exportable' }
    }, {
        'extend': 'print',
        'className': 'btn btn-primary btn-comparison-print',
        'exportOptions': { 'columns': '.exportable' },
        'autoPrint': false
    }];

    /**
     * Return a direction marker, <, =, or >.
     *
     * @function dir
     *
     * @param {integer} older - How many passages are older.
     * @param {integer} newer - How many passages are newer.
     *
     * @return Direction marker.
     */

    function dir(older, newer) {
        if (older > newer) {
            return '>';
        }
        if (older < newer) {
            return '<';
        }
        return '=';
    }

    /**
     * Row conversion function.  Convert numeric values to numeric types and add
     * calculated fields.
     *
     * @function main_row_conversion
     *
     * @return The converted row
     */

    function main_row_conversion(d) {
        return {
            'range': d.range,
            'length1': +d.length1,
            'length2': +d.length2,
            'common': +d.common,
            'equal': +d.equal,
            'older': +d.older,
            'newer': +d.newer,
            'norel': +d.norel,
            'unclear': +d.unclear,
            'affinity': Math.round(d.affinity * 100000) / 1000,
            'rank': +d.rank,
            'direction': dir(+d.older, +d.newer)
        };
    }

    /**
     * Detail row conversion function.  Convert numeric values to numeric types
     * and add calculated fields.
     *
     * @function detail_row_conversion
     *
     * @return The converted row
     */

    function detail_row_conversion(d) {
        return {
            'pass_id': d.pass_id,
            'pass_hr': d.pass_hr,
            'labez_clique1': d.labez_clique1,
            'lesart1': d.lesart1,
            'labez_clique2': d.labez_clique2,
            'lesart2': d.lesart2,
            'older': d.older === 'True',
            'newer': d.newer === 'True',
            'norel': d.norel === 'True',
            'unclear': d.unclear === 'True'
        };
    }

    /**
     * Initialize the details table structure.  This has to be done only once.
     * On navigation we'll throw all detail tables away.
     *
     * @function init_details_table
     *
     * @param {jQuery} $detailsTable - The details table root node, which is not
     * really a table node but a tr node containing a table further down.
     */

    function init_details_table($detailsTable) {
        var buttons = default_buttons.slice();
        var caption = $('caption span.caption', $detailsTable).text().replace(/\s+/g, ' ');
        buttons[1].filename = caption;
        buttons[2].title = caption;
        var details_table = $detailsTable.find('table').DataTable( // eslint-disable-line new-cap
        $.extend({}, default_table_options, {
            'columns': [{
                'data': function data(r, type /* , val, meta */) {
                    if (type === 'sort') {
                        return tools.natural_sort(r.pass_id);
                    }
                    return '<a href="coherence#' + r.pass_id + '">' + r.pass_hr + '</a>';
                },
                'class': 'passage'
            }, {
                'data': 'lesart1',
                'class': 'lesart lesart1'
            }, {
                'data': 'labez_clique1',
                'class': 'ms ms1'
            }, {
                'data': null,
                'class': 'direction',
                'render': function render(r) {
                    if (r.older) {
                        return '>';
                    }
                    if (r.newer) {
                        return '<';
                    }
                    if (r.unclear) {
                        return '?';
                    }
                    return '< >';
                }
            }, {
                'data': 'labez_clique2',
                'class': 'ms ms2'
            }, {
                'data': 'lesart2',
                'class': 'lesart lesart2'
            }],
            'order': [[0, 'asc']],
            'createdRow': function createdRow(r, d /* , index */) {
                var $row = $(r);
                $row.toggleClass('newer', d.newer);
                $row.toggleClass('older', d.older);
            },
            'buttons': {
                'buttons': buttons,
                'dom': {
                    'container': {
                        'className': 'btn-group btn-group-xs'
                    }
                }
            }
        }));

        details_table.buttons().container().appendTo($('div.toolbar-comparison-detail', $detailsTable));
        return details_table;
    }

    /**
     * Opens a table containing a detailed view of one range.
     *
     * @function toggle_details_table
     */

    function toggle_details_table() {
        var $tr = $(this).closest('tr');
        var $table = $tr.closest('table');
        var table = $table.DataTable(); // eslint-disable-line new-cap
        var row = table.row($tr);

        if (row.child.isShown()) {
            $('div.slider', row.child()).slideUp(function () {
                row.child.hide();
                $tr.removeClass('shown');
            });
        } else {
            if ($tr.hasClass('csv-loaded')) {
                $tr.addClass('shown');
                row.child.show();
                $('div.slider', row.child()).slideDown();
                return;
            }

            var params2 = {
                'ms1': module.ms1.hsnr,
                'ms2': module.ms2.hsnr,
                'range': $tr.attr('data-range')
            };

            var $detailsTable = create_details_table(module.ms1.hs, module.ms2.hs, params2.range);
            row.child($detailsTable, 'no-padding').show();
            $tr.addClass('shown');

            d3.csv('comparison-detail.csv?' + $.param(params2), detail_row_conversion, function (error, csv) {
                if (error) {
                    throw error;
                }
                $tr.addClass('csv-loaded');
                var details_table = init_details_table($detailsTable);
                details_table.clear().rows.add(csv).draw();
                $('div.slider', row.child()).slideDown();
            });
        }
    }

    /**
     * Return a skeleton for the main table.
     *
     * @function create_main_table
     *
     * @return {jQuery} The HTML skeleton.
     */

    function create_main_table() {
        return $('\n            <table class="comparison table table-bordered table-condensed table-hover" cellspacing="0">\n              <thead>\n                <tr>\n                  <th class="details-control"></th>\n\n                  <th class="range exportable">Chapter</th>\n                  <th class="direction exportable">Dir</th>\n                  <th class="rank exportable">NR</th>\n\n                  <th class="perc exportable">Perc</th>\n                  <th class="eq exportable">Eq</th>\n                  <th class="common exportable">Pass</th>\n\n                  <th class="newer exportable">W1&lt;W2</th>\n                  <th class="older exportable">W1&gt;W2</th>\n                  <th class="uncl exportable">Uncl</th>\n                  <th class="norel exportable">NoRel</th>\n                  <!--\n                    <th class="length length1 exportable">W1 defined</th>\n                    <th class="length length2 exportable">W2 defined</th>\n                  -->\n                </tr>\n              </thead>\n              <tbody>\n              </tbody>\n            </table>');
    }

    /**
     * Return a skeleton for a drill-down table.
     *
     * @function create_details_table
     *
     * @param {string} ms1   - Name of the first manuscript to compare.
     * @param {string} ms2   - Name of the second manuscript to compare.
     * @param {string} range - The range to compare.
     *
     * @return {jQuery} The HTML skeleton.
     */

    function create_details_table(ms1, ms2, range) {
        return $('\n            <tr class="no-padding">\n              <td class="no-padding"></td>\n              <td class="no-padding" colspan="12">\n                <div class="slider">\n                  <table cellspacing="0" width="100%"\n                          class="comparison-detail table table-bordered table-condensed table-hover">\n                    <caption>\n                      <span class="caption">\n                        Comparison of ' + ms1 + ' and ' + ms2 + ' in Chapter ' + range + '\n                      </span>\n                      <div class="btn-toolbar toolbar toolbar-comparison-detail" role="toolbar">\n                      </div>\n                    </caption>\n                    <thead>\n                      <tr>\n                        <th class="passage exportable">Passage</th>\n                        <th class="lesart lesart1 exportable">Lesart</th>\n                        <th class="ms ms1 exportable">' + ms1 + '</th>\n                        <th class="direction exportable">Dir</th>\n                        <th class="ms ms2 exportable">' + ms2 + '</th>\n                        <th class="lesart lesart2 exportable">Lesart</th>\n                      </tr>\n                    </thead>\n                  </table>\n                </div>\n              </td>\n            </tr>\n        ');
    }

    /**
     * Initialize the main table structure.  This has to be done only once.  On
     * navigation we only replace the table data.
     *
     * @function init_main_table
     */

    function init_main_table() {
        var $table = create_main_table();
        $table.appendTo($('div.panel-comparison'));
        var $tbody = $table.find('tbody');

        var table = $table.DataTable($.extend({}, default_table_options, { // eslint-disable-line new-cap
            'columns': [{
                'class': 'details-control',
                'orderable': false,
                'data': null,
                'defaultContent': ''
            }, {
                'data': function data(r, type /* , val, meta */) {
                    if (type === 'sort') {
                        return tools.natural_sort(r.range);
                    }
                    return r.range;
                },
                'class': 'range'
            }, {
                'data': 'direction',
                'class': 'direction'
            }, {
                'data': 'rank',
                'class': 'equal'
            }, {
                'data': 'affinity',
                'class': 'equal'
            }, {
                'data': 'equal',
                'class': 'equal'
            }, {
                'data': 'common',
                'class': 'common'
            }, {
                'data': 'newer',
                'class': 'newer'
            }, {
                'data': 'older',
                'class': 'older'
            }, {
                'data': 'unclear',
                'class': 'unclear'
            }, {
                'data': 'norel',
                'class': 'norel'
            }],
            'order': [[1, 'asc']],
            'createdRow': function createdRow(row, data, dummy_index) {
                var $row = $(row);
                $row.attr('data-range', data.range);
                $row.toggleClass('older', data.older > data.newer);
                $row.toggleClass('newer', data.older < data.newer);
            },
            'buttons': {
                'buttons': default_buttons,
                'dom': {
                    'container': {
                        'className': 'btn-group btn-group-xs'
                    }
                }
            }
        }));

        table.buttons().container().appendTo($('div.toolbar-comparison'));

        $tbody.on('click', 'td.details-control', toggle_details_table);
    }

    /**
     * Called after navigation.  Redraws the whole page.
     *
     * @function on_navigation
     */

    function on_navigation() {
        var hash = window.location.hash.substring(1);
        if (hash) {
            var p = tools.deparam(hash);

            var p1 = $.getJSON('manuscript.json/' + p.ms1, function (json) {
                module.ms1 = json.data;
            });
            var p2 = $.getJSON('manuscript.json/' + p.ms2, function (json) {
                module.ms2 = json.data;
            });

            $.when(p1, p2).done(function () {
                // update the input form
                var $form = $('form.manuscripts-selector');
                $('input[name="ms1"]', $form).val(module.ms1.hs + '.');
                $('input[name="ms2"]', $form).val(module.ms2.hs + '.');

                // update the headers
                var caption = tools.format('Comparison of {ms1} and {ms2}', {
                    'ms1': module.ms1.hs,
                    'ms2': module.ms2.hs
                });
                $('title').text(caption);
                $('h1 span.caption').text(caption);
                $('div.panel-comparison-header span.caption').text(caption);

                // reload table
                var url = 'comparison-summary.csv?' + $.param({
                    'ms1': module.ms1.hsnr,
                    'ms2': module.ms2.hsnr
                });
                d3.csv(url, main_row_conversion, function (error, csv) {
                    if (error) {
                        throw error;
                    }
                    var table = $('table.comparison');
                    var data_table = table.DataTable(); // eslint-disable-line new-cap
                    data_table.clear().rows.add(csv).draw();
                    /*
                    table.find ('th.older').text   (module.ms1.hs + ' older');
                    table.find ('th.newer').text   (module.ms2.hs + ' older');
                    table.find ('th.length1').text (module.ms1.hs + ' defined');
                    table.find ('th.length2').text (module.ms2.hs + ' defined');
                    */
                });
            });
        }
    }

    /**
     * Init the navigation elements.  Also listen for hashtag events.
     *
     * @function init_nav
     */

    function init_nav() {
        function fix(s) {
            var re = /^\d+$/;
            s += '';
            if (re.test(s) && s.length < 6) {
                return s + '.';
            }
            return s;
        }

        // User hit 'Go'
        $('form.manuscripts-selector').on('submit', function (event) {
            var q = $(event.currentTarget).serializeArray();
            q[0].value = fix(q[0].value);
            q[1].value = fix(q[1].value);
            window.location.hash = '#' + $.param(q);
            event.preventDefault();
        });

        // From above or user hit back-button, etc.
        $(window).on('hashchange', function () {
            $(document).trigger('ntg.comparison.changed');
        });

        // Hook
        $(document).on('ntg.comparison.changed', function () /* event */{
            on_navigation();
        });
    }

    /**
     * Initialize the module.
     *
     * @function init
     */
    function init() {
        init_nav();
        init_main_table();
        on_navigation();
    }

    module.init = init;
    return module;
});

//# sourceMappingURL=comparison.js.map