/*!
    Copyright (C) 2015 Google Inc., authors, and contributors <see AUTHORS file>
    Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
    Created By: dandv@google.com
    Maintained By: dandv@google.com
*/


/**

@author Dan Dascalescu, [@dandv](http://dandascalescu.com)
@overview # Normalize the GGRC REST API

This module is the interface to the GGRC REST API. It provides access to GGRC objects, and formats
the response objects to a simple, linear model, from the complex hierarchical/proxy model that comes
from the wire. Why this is done is explained below.

## GGRC mappings

The [GGRC Developer Guide](https://docs.google.com/document/d/1EscGXLotIvpoaJXcKiG64ixk48zSBFYY32qKsiFUS4I/edit#heading=h.whrtic6858g8)
mentions eight types of mappings. "Mapping" means most of the time a [1-to-1 relationship](https://en.wikipedia.org/wiki/Map_(higher-order_function),
such as a function that transforms (or maps) a list of number to a list of their squares.

The GGRC community has been using the word "mapping" to mean *link* or *relationship*, e.g. Program has Controls.
Most of these eight types of mappings are TBD, but the most common ones are Direct and Proxy:

> Direct: A direct mapping is a relationship where one model directly references another model.
> E.g. Sections contain a `directive` attribute, so Section has a Direct mapping to Directive.

This is simple, clear, and convenient.

> Proxy: A proxy mapping is a relationship where one model references another through another
> “join” or “proxy” model. E.g., Programs reference Controls via the ProgramControl join/proxy model.
> The Proxy mapping specifies the attributes and models involved in the relationship

This introduces an extra step when rendering the relationships between objects in a UI.

The other mappings are Indirect (inconsistent with the other mappers), Search (TBD),
Multi, TypeFilter (TBD), CustomFilter (TBD) and Cross.

This multitude of mappings [has caused confusion to end users](https://docs.google.com/document/d/1Gr3ohHyeLjMxE0JEJ12ga6RefZS6Eqk_kQAzBACgjR4):

> Current implementation and rules around mappings is unclear and confusing to end users. Also,
> inconsistency brought a lot of user reported bugs, which are currently scoped to over 300
> development hours. If we attend all these bugs, we would clear out symptoms, but not the core problem.

What this means when it comes to implement a UI is that you can't ask the API for a simple list of
the objects related (aka "mapped") to a given one and get it in an array.  Instead, the API groups
different objects under different keys, and for most of them, it makes you jump through an additional
hoop, the proxy mapping. See for example [what a Control looks like](https://gist.github.com/dandv/8794f5add6bcc0e11359#file-api-controls-18-json).

While implementing the Webix UI, there has been no need, so far, for proxy mappings. These may be an
artifact the GGRC data model having been designed for a RDBMS (MySQL) when in actuality GGRC data is
an object graph better suited for an object-oriented database like MongoDB or RethinkDB.

Besides this major problem, here are some GGRC REST API idiosyncrasies:

* The API endpoints are lowercase plurals, e.g. "risk_assessments". But the type of each object is
  Title Case singular, e.g. "Risk Assessment".
  In other words, what you get from one endpoint, you can't use for another.
* Types like "Policy" or "Process" aren't pluralizable by adding an 's', but that's forgivable
* The API has a /people endpoint, but all endpoints return "Person" as a type. /persons is not a valid endpoint.
* Every other object has a "title" attribute, but people (or persons) have a "name" attribute instead.
* Requests for multiple objects, say "programs" return the array of objects in
  programs_collection.programs, as if 'programs' alone wasn't OK
* Control objects (and probably others) have both an "assertions" and an "assertations" array.


Note that an object has a type, e.g. Program, and a kind, e.g. Directive. A Program is a kind of Directive.
*/

/**
 * TODO:
 * http://usejsdoc.org/howto-commonjs-modules.html
 * http://css.dzone.com/articles/introduction-jsdoc
 */

/**
 * @namespace RESTAPI
 */
var RESTAPI = (function () {

    var apiRoot = '/api/';
    var searchRoot = '/search/';
    var stopPromise = new Promise(function stopPromise() {});


    /**
     * Title Case: "risk assessments" -> "Risk Assessments"
     * @memberOf RESTAPI
     * @param {String} string - The string to transform to title case
     */
    function toTitleCase(string) {
        return string.replace(/\w\S*/g, function (txt){
            return txt.charAt(0).toUpperCase() + txt.substr(1).toLowerCase();
        });
    }

    /**
     * Return the singular of a type plural, e.g. Facilities -> Facility
     * @param type
     * @returns {string}
     */
    function typePlural2Singular(type) {  // lifted straight from application.js / cms_singularize
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
    }

    /**
     * "Org Groups" -> "org_groups", suitable as a REST API endpoint name
     * @memberOf RESTAPI
     * @param {String} type - A Type such as "Org Groups" or "People"
     */
    function typePlural2ApiPlural(type) {
        type = type.replace(' ', '_', 'g').toLowerCase().trim();
        return type;
    }

    /**
     * Transform "risk_assessments" -> "Risk Assessments"
     * @memberOf RESTAPI
     * @param type
     */
    function apiPlural2typePlural(type) {
        type = toTitleCase(type.replace('_', ' ', 'g'));
        return type;
    }

    /**
     * Transform Facility -> facilities, RiskAssessment -> risk_assessments, Program -> programs
     * @memberOf RESTAPI
     * @param {String} type - A type like "Risk Assessment"
     */
    function typeSingular2apiPlural(type) {
        return (type + 's')
            .replace(/ys$/, 'ies')  // Facilitys -> Facilities
            .replace(/sss$/, 'sses')  // Processs -> Processes
            .replace(/([a-z])([A-Z])/g, '$1_$2')  // OrgGroups -> Org_Groups
            .toLowerCase();
    }

    /**
     * Get/reify an object from the server.
     * @memberOf RESTAPI
     * @param type - e.g. 'programs' or 'risk_assessments'. Must be an API plural name.
     * @param id - database ID of the object
     * @param [fields] - Limits the fields retrieved from the objects to those in this comma-separated list
     * @returns {*} Promise. Use it as getObject('programs', '2935').then(function (data) { ... });
     */
    function getObject(type, id, fields) {
        var parameters = {};
        if (fields) parameters.__fields = fields;
        return webix.ajax().header({
            'Accept': 'application/json'
        }).get('/api/' + type + '/' + id, parameters);
    }

    /**
     * Gets the objects of a given type with the given ids. Optionally return only the specified fields.
     * @memberOf RESTAPI
     * @param {String} type - Object type, e.g. 'programs' or 'risk_assessments'. Must be an API plural name.
     * @param {String[]} ids - array of object ids
     * @param {String} [fields] - Limits the fields retrieved from the objects to those in this comma-separated list. E.g. 'id,title,private' for the LHN tree.
     * @param {Boolean} [sync=false] - Perform this request synchronously and wait for result (true), or async (false)
     * @returns {*} Promise. Use it as getObjects(...).then(function (data) { ...data.json()... }).fail(function (error) {...});
     */
    function getObjects(type, ids, fields, sync) {
        var parameters = {
            id__in: ids  // TODO paging
        };
        if (fields) parameters.__fields = fields;
        var ajax = sync? webix.ajax().sync() : webix.ajax();
        if (type.match(/^related/)) type = 'relationships';  // just another API inconsistency: related_destinations is not a valid endpoint
        return ajax.header({
            'Accept': 'application/json'
        }).get('/api/' + type, parameters);
    }

    /**
     * Gets the objects of a given type that are related ("mapped") to the given object.
     * @memberOf RESTAPI
     * @param {Object} object - the object for which we want to get the mapped objects. Must have a <type> key
     * @param {String} type - The type of related objects we're looking for, e.g. 'programs' or 'risk_assessments'. Must be an API plural name.
     * @param {String} [fields] - Limits the fields retrieved from the objects to those in this comma-separated list. E.g. 'id,title,private' for the LHN tree.
     * @param {Boolean} [sync=false] - Perform this request synchronously and wait for result (true), or async (false)
     * @returns {*} Promise. Use it as getRelatedObjects(...).then(function (data) { ...data.json()... }).fail(function (error) {...});
     */
    function getRelatedObjects(object, type, fields, sync) {
        if (type in object && object[type].length) {
            var relatedIds = object[type].map(function (object) { return object.id; });
            return getObjects(type, relatedIds, fields, sync);
        }
        return sync? [] : stopPromise;
    }

    /**
     * When they come from the API, objects have various related objects grouped under keys like
     * `directives` or `related_destinations`. This is caused largely by proxy mappings, and makes
     * it painful to present different object types with common fields in the same format, e.g. a grid.

     * @memberOf RESTAPI
     * @param {Object} object - An object as received from the REST API
     * @returns {Object} - The object is modified (made sane) and returned. E.g. a program will have a
     * `regulations` key that's an array, not a `directives[]` key with some objects being regulations
     * and other being contracts, policies or standards.
     */
    function normalizeObject(object) {
        // TODO make nulls undefined to avoid this Webix bug: http://forum.webix.com/discussion/3700/bug-datatable-treetable-can-t-export-cells-with-null-values
        // move to the root level any "directive"-type objects (why are they under the "directives" key anyway?)
        object.directives && object.directives.forEach(function (directive) {
            // regulations, contracts, policies, standards and probably programs too; also stored in program_directives in some way
            // each has fields like: `href: "/api/policies/5938"`, `id: 5938`, `type: "Policy"`
            var plural = typeSingular2apiPlural(directive.type);
            plural in object? object[plural].push(directive) : object[plural] = [directive];
        });

        // related_destinations: systems, processes, data assets, products, projects, facilities, markets, org groups, vendors
        var data = getRelatedObjects(object, 'related_destinations', 'destination', 'sync mode');
        if (data.responseText) try {
            data = JSON.parse(data.responseText);
            // the response looks like this: https://gist.github.com/dandv/8794f5add6bcc0e11359#file-relationships_destinations-json
            // move the objects in the `relationships` array to corresponding root-level API-pluralized keys of object
            data.relationships_collection.relationships.forEach(function (destination) {
                destination = destination.destination;  // Destination's Child
                var type = typeSingular2apiPlural(destination.type);
                type in object ? object[type].push(destination) : object[type] = [destination];
            });
        } catch (e) {
            console.error('Could not parse related_destinations for', object.type, object.id);
            webix.message('Could not parse related_destinations for ' + object.type + ' ' + object.id);
        }

        // TODO delete the original keys
        /*people & object_people - excludes the task contact & modified_by - those are implicitly added to the People tab
         workflow tasks is synthetically computed*/

        /* control 18 - https://gist.github.com/dandv/8794f5add6bcc0e11359#file-api-controls-18-json
         sections: 4; 2 of the sections are "type": "Clause", the other 2 are indeed "type": "Section"
         control_sections: 4, "type": "ControlSection"
         programs & program_controls: 4, consistent type
         directive_controls: 6
         control_controls: 6
         object_controls: 1
         directive: 1 (policy, object)
         implementing_control_controls: 1
         objective_controls: 1
         objectives: 1
         object_people: 1
         owners: 1, "type": "Person"
         object_owners: 1, "type": "ObjectOwner"
         contact: 1, "type": "Person"
         kind: null (!... because a control is not a directive or related_destination, I guess?)
         */
        return object;
    }


    /**
     * Normalize a set of objects returned by an API call that takes id__in,
     * such as https://gist.github.com/dandv/8794f5add6bcc0e11359#file-api-programs-id__in-2935-2806-json
     *
     * @memberOf RESTAPI
     * @param {object} data
     * @returns {Object[]}
     */
    function normalizeObjects(data) {
        var collection = Object.keys(data)[0];  // e.g. risk_assessments_collection
        console.assert(Object.keys(data).length === 1, 'Unsupported API result. Please report. Data was: ' + JSON.stringify(data));  // TODO report effectively
        var type = collection.replace('_collection', '');  // e.g. risk_assessments
        var relatedObjects = data[collection][type];

        // calculate which objects have others related to them (probably all)
        relatedObjects.forEach(function (object) {
            // TODO object = normalizeObject(object); ?
            // TODO actually check the sum of the lengths of the related objects arrays
            object.webix_kids = true;
            object.icon = type;
        });
        return relatedObjects;
    }

    return {
        toTitleCase: toTitleCase,
        typePlural2Singular: typePlural2Singular,
        typePlural2ApiPlural: typePlural2ApiPlural,
        apiPlural2typePlural: apiPlural2typePlural,
        typeSingular2apiPlural: typeSingular2apiPlural,
        getObject: getObject,
        getObjects: getObjects,
        getRelatedObjects: getRelatedObjects,
        normalizeObject: normalizeObject,
        normalizeObjects: normalizeObjects
    };
})();
