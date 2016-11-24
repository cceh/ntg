/* globals module, process, require */

var Autoprefix = require ('less-plugin-autoprefix');

module.exports = function (grunt) {
    'use strict';

    var py_files = ['**/*.py'];

    var afs =  grunt.option ('afs') || process.env.GRUNT_NTG_AFS || '/afs/rrz/vol/www/projekt/ntg';

    var localfs = grunt.option ('localfs') || process.env.GRUNT_NTG_LOCALFS ||
        '/var/www/ntg';

    var git_user = grunt.option ('gituser') || process.env.GRUNT_NTG_GITUSER;

    var browser = grunt.option ('browser') || process.env.GRUNT_BROWSER || 'iceweasel';

    grunt.initConfig ({
        'afs'     : afs,
        'localfs' : localfs,
        'browser' : browser,
        'rsync'   : 'rsync -rlptz --exclude="*~" --exclude=".*" ' +
                    '--exclude="*.less" --exclude="node_modules"',
        'gituser' : git_user,
        'pkg'     : grunt.file.readJSON ('package.json'),

        'less' : {
            'options' : {
                'banner'  : '/* Generated file. Do not edit. */\n',
                'plugins' : [
                    new (Autoprefix) ({ 'browsers': ['last 2 versions'] }),
                ],
            },
            'production' : {
                'files' : [
                    {
                        'expand' : true,
                        'src'    : ['server/static/css/**/*.less'],
                        'ext'    : '.css',
                        'extDot' : 'last',
                    },
                ],
            },
        },

        'pylint' : {
            'options' : {
                'force' : true,
            },
            'server'  : ['server/**/*.py'],
            'scripts' : ['scripts/cceh/**/*.py'],
        },

        'csslint' : {
            'options' : {
                'adjoining-classes'      : false,   // concerns IE6
                'box-sizing'             : false,   // concerns IE6,7
                'ids'                    : false,
                'overqualified-elements' : false,
                'qualified-headings'     : false,
            },
            'src' : ['server/static/css/**/*.css'],
        },

        'pot' : {
            'options' : {
                'text_domain' : 'ntg',
                'encoding'    : 'utf-8',
                'dest'        : 'languages/',
                'keywords'    : ['__', '_e', '_n:1,2', '_x:1,2c'],
                'msgmerge'    : true,
            },
            'files' : {
                'src'    : py_files,
                'expand' : true,
            },
        },

        'potomo' : {
            'themes' : {
                'options' : {
                    'poDel' : false,
                },
                'files' : [{
                    'expand' : true,
                    'src'    : ['languages/*.po'],
                    'dest'   : './',
                    'ext'    : '.mo',
                    'nonull' : true,
                }],
            },
        },

        'shell' : {
            'options' : {
                'cwd'         : '.',
                'failOnError' : false,
            },
            'eslint' : {
                'command' :
                './node_modules/.bin/eslint -f unix Gruntfile.js server/static/js/*.js',
            },
            'jshint' : {
                'command' :
                'jshint --reporter=./jshint-reporter-emacs.js Gruntfile.js server/static/js/*.js',
            },
            'jsdoc' : {
                // http://usejsdoc.org/about-commandline.html
                'command' :
                'jsdoc -d jsdoc -a all server/static/js/*.js',
            },
        },

        'watch' : {
            'files' : ['<%= less.production.files %>'],
            'tasks' : ['less'],
        },
    });

    grunt.loadNpmTasks ('grunt-contrib-csslint');
    grunt.loadNpmTasks ('grunt-contrib-less');
    grunt.loadNpmTasks ('grunt-contrib-watch');
    grunt.loadNpmTasks ('grunt-pot');
    grunt.loadNpmTasks ('grunt-potomo');
    grunt.loadNpmTasks ('grunt-pylint');
    grunt.loadNpmTasks ('grunt-shell');

    grunt.registerTask ('lint',       ['pylint', 'shell:eslint']);
    grunt.registerTask ('mo',         ['pot', 'potomo']);
    grunt.registerTask ('doc',        ['shell:jsdoc']);

    grunt.registerTask ('default',    ['shell:eslint', 'less']);
};
