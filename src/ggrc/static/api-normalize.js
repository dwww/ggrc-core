/*

Normalize the GGRC REST API

Here are some GGRC REST API idiosyncrasies:

    * The API endpoints are lowercase plurals, e.g. risk_assessments. But the type of each object is Title Case singular, e.g. Risk Assessment.
      In other words, what you get from one endpoint, you can't use for another.
    * Types like "Policy" aren't pluralizable by adding an 's', but that's forgivable
    * The API has a /people endpoint, but all endpoints return "Person" as a type. /persons is not a valid endpoint.
    * Every other object has a "title" attribute, but people (or persons) have a "name" attribute instead.
    * Requests for multiple objects, say "programs" return the array of objects in programs_collection.programs, as if 'programs' alone wasn't OK

 */


//  TODO lifted straight from application.js, which maybe we want to load... or not
window.cms_singularize = function(type) {
    type = type.trim();
    var _type = type.toLowerCase();
    switch(_type) {
        case "facilities":
        type = type[0] + "acility"; break;
        case "people":
        type = type[0] + "erson"; break;
        case "processes":
        type = type[0] + "rocess"; break;
        case "policies":
        type = type[0] + "olicy"; break;
        case "systems_processes":
        type = type[0] + "ystem_" + type[8] + "rocess";
        break;
        default:
        type = type.replace(/s$/, "");
    }

    return type.replace(' ', '', 'g');
};

// library: https://github.com/gouch/to-title-case/blob/master/to-title-case.js
function toTitleCase(string) {
    return string.replace(/\w\S*/g, function(txt){return txt.charAt(0).toUpperCase() + txt.substr(1).toLowerCase();})
}

/**
 * `Org Groups` -> `org_groups`, suitable as a REST API endpoint name
 * @param type
 */
function typePlural2ApiPlural(type) {
    type = type.replace(' ', '_', 'g').toLowerCase().trim();
    // ?? TODO rm: if (type === 'people') type = 'persons';  // naming was hard, and now we have to deal with that
    return type;
}

/**
 * risk_assessments -> Risk Assessments
 * @param type
 */
function apiPlural2typePlural(type) {
    type = toTitleCase(type.replace('_', ' ', 'g'));
    return type;
}

/**
 * Facility -> facilities, RiskAssessment -> risk_assessments, Program -> programs
 */
function typeSingular2apiPlural(type) {
    return (type + 's').replace(/ys$/, 'ies').replace(/([a-z])([A-Z])/g, '$1_$2').toLowerCase();
    // TODO space/_
}
