requirejs.config ({
    'urlArgs' : 'bust=' + server_start_time,
    'paths'   : {
        // public libs
        'bootstrap'                    : '/static/bower_components/bootstrap/dist/js/bootstrap',
        'jquery'                       : '/static/bower_components/jquery/dist/jquery',
        'jquery-ui'                    : '/static/bower_components/jquery-ui/jquery-ui',
        'd3'                           : '/static/bower_components/d3/d3',
        'd3-promise'                   : '/static/bower_components/d3.promise/dist/d3.promise',
        'bootstrap-slider'             : '/static/bower_components/seiyria-bootstrap-slider/dist/bootstrap-slider',
        'lodash'                       : '/static/bower_components/lodash/lodash',
        'datatables.net'               : '/static/bower_components/datatables.net/js/jquery.dataTables',
        'datatables.net-bs'            : '/static/bower_components/datatables.net-bs/js/dataTables.bootstrap',
        'datatables.net-buttons'       : '/static/bower_components/datatables.net-buttons/js/dataTables.buttons',
        'datatables.net-buttons-bs'    : '/static/bower_components/datatables.net-buttons-bs/js/buttons.bootstrap',
        'datatables.net-buttons-html5' : '/static/bower_components/datatables.net-buttons/js/buttons.html5',
        'datatables.net-buttons-print' : '/static/bower_components/datatables.net-buttons/js/buttons.print',
        'urijs'                        : '/static/bower_components/urijs/src',
        'pegjs'                        : '/static/bower_components/pegjs/peg-0.10.0',
        'rsvp'                         : '/static/bower_components/rsvp.js/rsvp',
        'text'                         : '/static/bower_components/requirejs-text/text',
        'css'                          : '/static/bower_components/require-css/css',
        // private libs
        'coherence'                    : '/static/js/coherence',
        'comparison'                   : '/static/js/comparison',
        'navigator'                    : '/static/js/navigator',
        'apparatus'                    : '/static/js/apparatus',
        'd3-stemma'                    : '/static/js/d3-stemma-layout',
        'd3-chord'                     : '/static/js/d3-chord-layout',
        'd3-common'                    : '/static/js/d3-common',
        'panel'                        : '/static/js/panel',
        'textflow'                     : '/static/js/textflow',
        'local-stemma'                 : '/static/js/local-stemma',
        'relatives'                    : '/static/js/relatives',
        'tools'                        : '/static/js/tools',
        // public css
        'bootstrap-css'                : '/static/bower_components/bootstrap/dist/css/bootstrap',
        'bootstrap-slider-css'         : '/static/bower_components/seiyria-bootstrap-slider/dist/css/bootstrap-slider',
        'jquery-ui-css'                : '/static/bower_components/jquery-ui/themes/smoothness/jquery-ui',
        'datatables-bs-css'            : '/static/bower_components/datatables.net-bs/css/dataTables.bootstrap',
        'datatables-buttons-bs-css'    : '/static/bower_components/datatables.net-buttons-bs/css/buttons.bootstrap',
        // private css
        'site-css'                     : '/static/css/site',
        'apparatus-css'                : '/static/css/apparatus',
        'coherence-css'                : '/static/css/coherence',
        'navigator-css'                : '/static/css/navigator',
        'comparison-css'               : '/static/css/comparison',
        'panel-css'                    : '/static/css/panel',
        'relatives-css'                : '/static/css/relatives',
        'textflow-css'                 : '/static/css/textflow',
        'ms_attesting-css'             : '/static/css/ms_attesting',
    },
    'shim' : {
        'bootstrap' : {
            // make sure jquery-ui gets loaded before bootstrap because we are
            // going to use noConflict () to remove bootstrap functions
            'deps' : ['jquery', 'jquery-ui'],
        },
    },
    // scripts/cceh/sri_hash <url>
    'sri' : {
        // 'jquery'         : 'sha256-16cdPddA6VdVInumRGo6IbivbERE8p7CQR3HzTBuELA=',
        // 'jquery-ui'      : 'sha256-n6soYSDuUZJzwagQnIMURozprKKpTPwVBCFtDeXFUqM=',
        // 'd3'             : 'sha256-fvARx0ln7Dg1l5tqFL4whDn33FU79YsN2V066eSXf3Q=',
    },
    'onNodeCreated' : function (node, config, module, dummy_path) {
        'use strict';

        if (config.sri[module]) {
            node.setAttribute ('integrity', config.sri[module]);
            node.setAttribute ('crossorigin', 'anonymous');
        }
    },
});
