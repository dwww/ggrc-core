/*!
    Copyright (C) 2014 Google Inc., authors, and contributors <see AUTHORS file>
    Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
    Created By: brad@reciprocitylabs.com
    Maintained By: brad@reciprocitylabs.com
*/

//= require can.jquery-all
//= require controls/control
//= require models/cacheable

can.Model.Cacheable("CMS.Models.SectionBase", {
    root_object: "section_base"
  , root_collection: "section_bases"
  , model_plural: "SectionBases"
  , table_plural: "section_bases"
  , title_plural: "Section Bases"
  , model_singular: "SectionBase"
  , title_singular: "Section Base"
  , table_singular: "section_base"
  , category: "governance"
  , root_model: "SectionBase"
  , findAll: "GET /api/section_bases"
  , findOne: "GET /api/section_bases/{id}"
  , create: "POST /api/section_bases"
  , update: "PUT /api/section_bases/{id}"
  , destroy: "DELETE /api/section_bases/{id}"
  , mixins : ["ownable", "contactable"]

  , model: function(params) {
      if (this.shortName !== 'SectionBase')
        return this._super(params);
      if (!params)
        return params;
      params = this.object_from_resource(params);
      if (!params.selfLink) {
        if (params.type !== 'SectionBase')
          return CMS.Models[params.type].model(params);
      }
      console.debug("Invalid SectionBase:", params);
    }

  , attributes: {
      context : "CMS.Models.Context.stub"
    , contact: "CMS.Models.Person.stub"
    , owners: "CMS.Models.Person.stubs"
    , modified_by: "CMS.Models.Person.stub"
    , object_people: "CMS.Models.ObjectPerson.stubs"
    , people: "CMS.Models.Person.stubs"
    , object_documents: "CMS.Models.ObjectDocument.stubs"
    , documents: "CMS.Models.Document.stubs"
    , object_controls: "CMS.Models.ObjectControl.stubs"
    , controls: "CMS.Models.Control.stubs"
    , directive: "CMS.Models.get_stub"
    , children: "CMS.Models.get_stubs"
    , control_sections: "CMS.Models.ControlSection.stubs"
    , directive_sections: "CMS.Models.DirectiveSection.stubs"
    , directives: "CMS.Models.get_stubs"
    , section_objectives: "CMS.Models.SectionObjective.stubs"
    , objectives: "CMS.Models.Objective.stubs"
    , object_sections: "CMS.Models.ObjectSection.stubs"
  }

  , init: function() {
    this._super.apply(this, arguments);
    this.validateNonBlank("title");
  }
}, {
});


CMS.Models.SectionBase("CMS.Models.Section", {
  root_object : "section"
  , root_collection : "sections"
  , model_plural : "Sections"
  , table_plural : "sections"
  , title_plural : "Sections"
  , model_singular : "Section"
  , title_singular : "Section"
  , table_singular : "section"
  , category : "governance"
  , root_model : "Section"
  , findAll : "GET /api/sections"
  , findOne : "GET /api/sections/{id}"
  , create : "POST /api/sections"
  , update : "PUT /api/sections/{id}"
  , destroy : "DELETE /api/sections/{id}"

  , attributes : {
      context : "CMS.Models.Context.stub"
    , contact : "CMS.Models.Person.stub"
    , owners : "CMS.Models.Person.stubs"
    , modified_by : "CMS.Models.Person.stub"
    , object_people : "CMS.Models.ObjectPerson.stubs"
    , people : "CMS.Models.Person.stubs"
    , object_documents : "CMS.Models.ObjectDocument.stubs"
    , documents : "CMS.Models.Document.stubs"
    , object_controls : "CMS.Models.ObjectControl.stubs"
    , controls : "CMS.Models.Control.stubs"
    , directive : "CMS.Models.get_stub"
    , children : "CMS.Models.get_stubs"
    , control_sections : "CMS.Models.ControlSection.stubs"
    , directive_sections: "CMS.Models.DirectiveSection.stubs"
    , directives: "CMS.Models.get_stubs"
    , section_objectives : "CMS.Models.SectionObjective.stubs"
    , objectives : "CMS.Models.Objective.stubs"
    , object_sections : "CMS.Models.ObjectSection.stubs"
    }

  , init: function() {
    this._super.apply(this, arguments);
    // Only Sections (not Clauses) need a parent Directive.
    this.validatePresenceOf("directive");
  }

  , tree_view_options : {
      show_view : "/static/mustache/sections/tree.mustache"
    , footer_view : GGRC.mustache_path + "/sections/tree_footer.mustache"
    , child_options : [{
        model : can.Model.Cacheable
      , mapping : "related_and_able_objects"
      , title_plural : "Business Objects"
      , draw_children : function(){
          return this.instance.type === "Objective";
        }
      , footer_view : GGRC.mustache_path + "/base_objects/tree_footer.mustache"
      , child_options : [{
            model: CMS.Models.Control
          , title_plural: "Controls"
          , mapping: "controls"
          , draw_children: false
          , footer_view: GGRC.mustache_path + "/controls/tree_footer.mustache"
          }]
      }]
    }

  , cache : can.getObject("cache", CMS.Models.SectionBase, true)
}, {
});


CMS.Models.SectionBase("CMS.Models.Clause", {
    root_object: "clause"
  , root_collection: "clauses"
  , model_plural: "Clauses"
  , table_plural: "clauses"
  , title_plural: "Clauses"
  , model_singular: "Clause"
  , title_singular: "Clause"
  , table_singular: "clause"
  , category: "governance"
  , root_model: "Clause"
  , findAll: "GET /api/clauses"
  , findOne: "GET /api/clauses/{id}"
  , create: "POST /api/clauses"
  , update: "PUT /api/clauses/{id}"
  , destroy: "DELETE /api/clauses/{id}"

  , attributes: {
      context : "CMS.Models.Context.stub"
    , contact: "CMS.Models.Person.stub"
    , owners: "CMS.Models.Person.stubs"
    , modified_by: "CMS.Models.Person.stub"
    , object_people: "CMS.Models.ObjectPerson.stubs"
    , people: "CMS.Models.Person.stubs"
    , object_documents: "CMS.Models.ObjectDocument.stubs"
    , documents: "CMS.Models.Document.stubs"
    , object_controls: "CMS.Models.ObjectControl.stubs"
    , controls: "CMS.Models.Control.stubs"
    , directive: "CMS.Models.get_stub"
    , children: "CMS.Models.get_stubs"
    , control_sections: "CMS.Models.ControlSection.stubs"
    , directive_sections: "CMS.Models.DirectiveSection.stubs"
    , directives: "CMS.Models.get_stubs"
    , section_objectives: "CMS.Models.SectionObjective.stubs"
    , objectives: "CMS.Models.Objective.stubs"
    , object_sections: "CMS.Models.ObjectSection.stubs"
  }

  , tree_view_options: {
      show_view: "/static/mustache/sections/tree.mustache"
    , footer_view: GGRC.mustache_path + "/sections/tree_footer.mustache"
    , child_options: [{
        model: can.Model.Cacheable
      , mapping: "related_and_able_objects"
      , title_plural: "Business Objects"
      , draw_children: function(){
          return this.instance.type === "Objective";
        }
      , footer_view: GGRC.mustache_path + "/base_objects/tree_footer.mustache"
      , child_options: [{
            model: CMS.Models.Control
          , title_plural: "Controls"
          , mapping: "controls"
          , draw_children: false
          , footer_view: GGRC.mustache_path + "/controls/tree_footer.mustache"
          }]
      }]
    }
  , cache : can.getObject("cache", CMS.Models.SectionBase, true)
}, {
});
