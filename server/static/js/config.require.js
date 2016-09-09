requirejs.config ({
    'paths' : {
        'bootstrap'      : '/static/bower_components/bootstrap/dist/js/bootstrap',
        'bootstrap3cdn'  : 'https://maxcdn.bootstrapcdn.com/bootstrap/3.3.6/js/bootstrap.min',
        'jquery'         : 'https://code.jquery.com/jquery-3.1.0',
        'jquery-migrate' : 'https://code.jquery.com/jquery-migrate-3.0.0',
        'jquery-ui'      : 'https://code.jquery.com/ui/1.12.0-rc.2/jquery-ui',
        'lodash'         : 'https://cdn.jsdelivr.net/lodash/4.13.1/lodash',
        'd3'             : 'https://d3js.org/d3.v4',
        'd3-common'      : '/static/js/d3-common',
        'd3-force'       : '/static/js/d3-force-layout',
        'd3-stemma'      : '/static/js/d3-passage-stemma-layout',
        'relatives'      : '/static/js/relatives',
        'coherence'      : '/static/js/coherence',
    },
    'shim' : {
        'bootstrap' : {
            'deps' : ['jquery'],
        },
    },
    // curl -s url | openssl dgst -sha256 -binary | openssl base64 -A
    'sri' : {
        'bootstrap3cdn'  : 'sha384-0mSbJDEHialfmuBBQP6A4Qrprq5OVfW37PRR3j5ELqxss1yVqOtnepnHVP9aJ7xS',
        // 'd3'             : 'sha256-fvARx0ln7Dg1l5tqFL4whDn33FU79YsN2V066eSXf3Q=',
        'jquery'         : 'sha256-slogkvB1K3VOkzAI8QITxV3VzpOnkeNVsKvtkYLMjfk=',
        'jquery-migrate' : 'sha256-lsVOB+3Yhm6He5MkTO3Bw/Xw4NXK7wYYTi1Y+M/2PrM=',
        'jquery-ui'      : 'sha256-6HSLgn6Ao3PKc5ci8rwZfb//5QUu3ge2/Sw9KfLuvr8=',
        'lodash'         : 'sha256-bebX2fvFHtRpmvraLHyf32TpGLK4ulZc2z7l5dLDW9Q=',
    },
    'onNodeCreated' : function (node, config, module, dummy_path) {
        'use strict';

        if (config.sri[module]) {
            node.setAttribute ('integrity', config.sri[module]);
            node.setAttribute ('crossorigin', 'anonymous');
        }
    },
});
