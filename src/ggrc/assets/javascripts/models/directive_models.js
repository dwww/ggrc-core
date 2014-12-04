/*!
    Copyright (C) 2014 Google Inc., authors, and contributors <see AUTHORS file>
    Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
    Created By: brad@reciprocitylabs.com
    Maintained By: brad@reciprocitylabs.com
*/

(function(can) {

can.Model.Cacheable("CMS.Models.Directive", {
  root_object : "directive"
  , root_collection : "directives"
  , category : "governance"
  // `rootModel` overrides `model.shortName` when determining polymorphic types
  , root_model : "Directive"
  , findAll : "/api/directives"
  , findOne : "/api/directives/{id}"
  , mixins : ["ownable", "contactable", "unique_title"]

  , model : function(params) {
      if (this.shortName !== 'Directive')
        return this._super(params);
      if (!params)
        return params;
      params = this.object_from_resource(params);
      if (!params.selfLink) {
        if (params.type !== 'Directive')
          return CMS.Models[params.type].model(params);
      } else {
        if (CMS.Models.Contract.meta_kinds.indexOf(params.kind) > -1)
          return CMS.Models.Contract.model(params);
        else if (CMS.Models.Regulation.meta_kinds.indexOf(params.kind) > -1)
          return CMS.Models.Regulation.model(params);
        else if (CMS.Models.Policy.meta_kinds.indexOf(params.kind) > -1)
          return CMS.Models.Policy.model(params);
        else if (CMS.Models.Standard.meta_kinds.indexOf(params.kind) > -1)
          return CMS.Models.Standard.model(params);
      }
      console.debug("Invalid Directive:", params);
    }

  , attributes : {
      context : "CMS.Models.Context.stub"
    , contact : "CMS.Models.Person.stub"
    , modified_by : "CMS.Models.Person.stub"
    , object_people : "CMS.Models.ObjectPerson.stubs"
    , people : "CMS.Models.Person.stubs"
    , object_documents : "CMS.Models.ObjectDocument.stubs"
    , documents : "CMS.Models.Document.stubs"
    , related_sources : "CMS.Models.Relationship.stubs"
    , related_destinations : "CMS.Models.Relationship.stubs"
    , object_objectives : "CMS.Models.ObjectObjective.stubs"
    , objectives : "CMS.Models.Objective.stubs"
    , program_directives : "CMS.Models.ProgramDirective.stubs"
    , directive_controls : "CMS.Models.DirectiveControl.stubs"
    , programs : "CMS.Models.Program.stubs"
    , directive_sections: "CMS.Models.DirectiveSection.stubs"
    , joined_sections: "CMS.Models.get_stubs"
    , sections : "CMS.Models.get_stubs"
    , controls : "CMS.Models.Control.stubs"
  }
  , defaults : {
  }
  , init : function() {
    this.validateNonBlank("title");
    //this.validateInclusionOf("kind", this.meta_kinds);
    this._super.apply(this, arguments);
  }
  , meta_kinds : []
  , links_to : { "Control" : "DirectiveControl", "Program" : "ProgramDirective" }
}, {
  init : function() {
    this._super && this._super.apply(this, arguments);
    var that = this;
  }
  , lowercase_kind : function() { return this.kind ? this.kind.toLowerCase() : undefined; }
});

CMS.Models.Directive("CMS.Models.Standard", {
    root_object : "standard"
  , root_collection : "standards"
  , model_plural : "Standards"
  , table_plural : "standards"
  , title_plural : "Standards"
  , model_singular : "Standard"
  , title_singular : "Standard"
  , table_singular : "standard"
  , findAll : "GET /api/standards"
  , findOne : "GET /api/standards/{id}"
  , create : "POST /api/standards"
  , update : "PUT /api/standards/{id}"
  , destroy : "DELETE /api/standards/{id}"
  , defaults : {
    kind : "Standard"
  }
  , tree_view_options : {
      list_view : GGRC.mustache_path + "/directives/tree.mustache"
    , footer_view : GGRC.mustache_path + "/directives/tree_footer.mustache"
    }
  , attributes : {
      context : "CMS.Models.Context.stub"
    , contact : "CMS.Models.Person.stub"
    , owners : "CMS.Models.Person.stubs"
    , modified_by : "CMS.Models.Person.stub"
    , object_people : "CMS.Models.ObjectPerson.stubs"
    , people : "CMS.Models.Person.stubs"
    , object_documents : "CMS.Models.ObjectDocument.stubs"
    , documents : "CMS.Models.Document.stubs"
    , related_sources : "CMS.Models.Relationship.stubs"
    , related_destinations : "CMS.Models.Relationship.stubs"
    , object_objectives : "CMS.Models.ObjectObjective.stubs"
    , objectives : "CMS.Models.Objective.stubs"
    , program_directives : "CMS.Models.ProgramDirective.stubs"
    , directive_controls : "CMS.Models.DirectiveControl.stubs"
    , programs : "CMS.Models.Program.stubs"
    , directive_sections: "CMS.Models.DirectiveSection.stubs"
    , joined_sections: "CMS.Models.get_stubs"
    , sections : "CMS.Models.get_stubs"
    , controls : "CMS.Models.Control.stubs"
  }
  , meta_kinds : [ "Standard" ]
  , cache : can.getObject("cache", CMS.Models.Directive, true)
}, {});

CMS.Models.Directive("CMS.Models.Regulation", {
  root_object : "regulation"
  , root_collection : "regulations"
  , model_plural : "Regulations"
  , table_plural : "regulations"
  , title_plural : "Regulations"
  , model_singular : "Regulation"
  , title_singular : "Regulation"
  , table_singular : "regulation"
  , findAll : "GET /api/regulations"
  , findOne : "GET /api/regulations/{id}"
  , create : "POST /api/regulations"
  , update : "PUT /api/regulations/{id}"
  , destroy : "DELETE /api/regulations/{id}"
  , defaults : {
    kind : "Regulation"
  }
  , tree_view_options : {
      list_view : GGRC.mustache_path + "/directives/tree.mustache"
    , footer_view : GGRC.mustache_path + "/directives/tree_footer.mustache"
    }
  , attributes : {
      context : "CMS.Models.Context.stub"
    , contact : "CMS.Models.Person.stub"
    , owners : "CMS.Models.Person.stubs"
    , modified_by : "CMS.Models.Person.stub"
    , object_people : "CMS.Models.ObjectPerson.stubs"
    , people : "CMS.Models.Person.stubs"
    , object_documents : "CMS.Models.ObjectDocument.stubs"
    , documents : "CMS.Models.Document.stubs"
    , related_sources : "CMS.Models.Relationship.stubs"
    , related_destinations : "CMS.Models.Relationship.stubs"
    , object_objectives : "CMS.Models.ObjectObjective.stubs"
    , objectives : "CMS.Models.Objective.stubs"
    , program_directives : "CMS.Models.ProgramDirective.stubs"
    , directive_controls : "CMS.Models.DirectiveControl.stubs"
    , programs : "CMS.Models.Program.stubs"
    , directive_sections: "CMS.Models.DirectiveSection.stubs"
    , joined_sections: "CMS.Models.get_stubs"
    , sections : "CMS.Models.get_stubs"
    , controls : "CMS.Models.Control.stubs"
  }
  , meta_kinds : [ "Regulation" ]
  , cache : can.getObject("cache", CMS.Models.Directive, true)
}, {});

CMS.Models.Directive("CMS.Models.Policy", {
  root_object : "policy"
  , root_collection : "policies"
  , model_plural : "Policies"
  , table_plural : "policies"
  , title_plural : "Policies"
  , model_singular : "Policy"
  , title_singular : "Policy"
  , table_singular : "policy"
  , findAll : "GET /api/policies"
  , findOne : "GET /api/policies/{id}"
  , create : "POST /api/policies"
  , update : "PUT /api/policies/{id}"
  , destroy : "DELETE /api/policies/{id}"
  , defaults : {
      kind : null
    }
  , tree_view_options : {
      list_view : GGRC.mustache_path + "/directives/tree.mustache"
    , footer_view : GGRC.mustache_path + "/directives/tree_footer.mustache"
    }
  , attributes : {
      context : "CMS.Models.Context.stub"
    , contact : "CMS.Models.Person.stub"
    , owners : "CMS.Models.Person.stubs"
    , modified_by : "CMS.Models.Person.stub"
    , object_people : "CMS.Models.ObjectPerson.stubs"
    , people : "CMS.Models.Person.stubs"
    , object_documents : "CMS.Models.ObjectDocument.stubs"
    , documents : "CMS.Models.Document.stubs"
    , related_sources : "CMS.Models.Relationship.stubs"
    , related_destinations : "CMS.Models.Relationship.stubs"
    , object_objectives : "CMS.Models.ObjectObjective.stubs"
    , objectives : "CMS.Models.Objective.stubs"
    , program_directives : "CMS.Models.ProgramDirective.stubs"
    , directive_controls : "CMS.Models.DirectiveControl.stubs"
    , programs : "CMS.Models.Program.stubs"
    , directive_sections: "CMS.Models.DirectiveSection.stubs"
    , joined_sections: "CMS.Models.get_stubs"
    , sections : "CMS.Models.get_stubs"
    , controls : "CMS.Models.Control.stubs"
  }
  , meta_kinds : [  "Company Policy", "Org Group Policy", "Data Asset Policy", "Product Policy", "Contract-Related Policy", "Company Controls Policy" ]
  , cache : can.getObject("cache", CMS.Models.Directive, true)
}, {});

CMS.Models.Directive("CMS.Models.Contract", {
  root_object : "contract"
  , root_collection : "contracts"
  , model_plural : "Contracts"
  , table_plural : "contracts"
  , title_plural : "Contracts"
  , model_singular : "Contract"
  , title_singular : "Contract"
  , table_singular : "contract"
  , findAll : "GET /api/contracts"
  , findOne : "GET /api/contracts/{id}"
  , create : "POST /api/contracts"
  , update : "PUT /api/contracts/{id}"
  , destroy : "DELETE /api/contracts/{id}"
  , defaults : {
    kind : "Contract"
  }
  , tree_view_options : {
      list_view : GGRC.mustache_path + "/directives/tree.mustache"
    , footer_view : GGRC.mustache_path + "/directives/tree_footer.mustache"
    }
  , attributes : {
      context : "CMS.Models.Context.stub"
    , contact : "CMS.Models.Person.stub"
    , owners : "CMS.Models.Person.stubs"
    , modified_by : "CMS.Models.Person.stub"
    , object_people : "CMS.Models.ObjectPerson.stubs"
    , people : "CMS.Models.Person.stubs"
    , object_documents : "CMS.Models.ObjectDocument.stubs"
    , documents : "CMS.Models.Document.stubs"
    , related_sources : "CMS.Models.Relationship.stubs"
    , related_destinations : "CMS.Models.Relationship.stubs"
    , object_objectives : "CMS.Models.ObjectObjective.stubs"
    , objectives : "CMS.Models.Objective.stubs"
    , program_directives : "CMS.Models.ProgramDirective.stubs"
    , directive_controls : "CMS.Models.DirectiveControl.stubs"
    , controls : "CMS.Models.Control.stubs"
    , programs : "CMS.Models.Program.stubs"
    , directive_sections: "CMS.Models.DirectiveSection.stubs"
    , joined_sections: "CMS.Models.get_stubs"
    , sections : "CMS.Models.get_stubs"
  }
  , meta_kinds : [ "Contract" ]
  , cache : can.getObject("cache", CMS.Models.Directive, true)
}, {});

})(this.can);
