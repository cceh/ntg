const _ = require ('lodash');

function formatter (results) {
    return _.flatMap (results, (result) => {
        return _.map (
            result.warnings,
            warning => `${result.source}:${warning.line}:${warning.column}: ${warning.severity}: ${warning.text}`
        );
    }).join ('\n');
}

module.exports = formatter;
