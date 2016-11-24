requirejs.config ({
    'paths' : {
        // public libs
        'bootstrap'        : '/static/bower_components/bootstrap/dist/js/bootstrap',
        'jquery'           : '/static/bower_components/jquery/dist/jquery',
        'jquery-ui'        : '/static/bower_components/jquery-ui/jquery-ui',
        'd3'               : '/static/bower_components/d3/d3',
        'd3-promise'       : '/static/bower_components/d3.promise/dist/d3.promise',
        'bootstrap-slider' : '/static/bower_components/seiyria-bootstrap-slider/dist/bootstrap-slider',
        'lodash'           : '/static/bower_components/lodash/lodash',
        'pegjs'            : '/static/bower_components/pegjs/peg-0.10.0',
        'rsvp'             : '/static/bower_components/rsvp.js/rsvp',
        'text'             : '/static/bower_components/requirejs-text/text',
        // private libs
        'coherence'        : '/static/js/coherence',
        'navigator'        : '/static/js/navigator',
        'apparatus'        : '/static/js/apparatus',
        'd3-force'         : '/static/js/d3-force-layout',
        'd3-stemma'        : '/static/js/d3-stemma-layout',
        'd3-common'        : '/static/js/d3-common',
        'textflow'         : '/static/js/textflow',
        'relatives'        : '/static/js/relatives',
        'tools'            : '/static/js/tools',
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
