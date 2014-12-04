/*!
    Copyright (C) 2014 Google Inc., authors, and contributors <see AUTHORS file>
    Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
    Created By: brad@reciprocitylabs.com
    Maintained By: brad@reciprocitylabs.com
*/

(function(can, $) {

can.Model.Cacheable("can.Model.Join", {
  join_keys : null
  , setup : function() {
    this._super.apply(this, arguments);
  }
  , init : function() {
    this._super && this._super.apply(this, arguments);
    function reinit(ev, instance) {
      if (instance instanceof can.Model.Join) {
        instance.reinit();
      //can.proxy(this, "reinit"));

        can.each(instance.constructor.join_keys, function(cls, key) {
          var obj;
          if (instance[key].reify && instance[key].reify().refresh)
            obj = instance[key].reify();
          else
            obj = cls.findInCacheById(instance[key].id);
          if (obj)
            obj.refresh();
        });
      }
    }
    if (this === can.Model.Join) {
      this.bind("created", reinit);
      this.bind("destroyed", reinit);
    }
  }
}, {
    init: function() {
      this._super.apply(this, arguments);
      var that = this;
      can.each(this.constructor.join_keys, function(cls, key) {
        that.bind(key + ".stub_destroyed", function() {
          // Trigger `destroyed` on self, since it was destroyed on the server
          that.destroyed();
        });
      });
    }

  , reinit : function() {
      this.init_join_objects();
    }

  , init_join_object_with_type: function(attr) {
      if(this[attr] instanceof can.Model) {
        return;
      }

      var object_id = this[attr + "_id"] || (this[attr] || {}).id
        , object_type = this[attr + "_type"] || (this[attr] || {}).type
        ;

      if (object_id && object_type && typeof object_type === "string") {
        this.attr(attr, CMS.Models.get_instance(
              object_type
            , object_id
            , this[attr]
            ) || this[attr]);
      } else if(object_id) {
        this.attr(attr, CMS.Models.get_instance(this[attr]));
      }
    }

  , init_join_object: function(attr, model_name) {
      var object_id = this[attr + "_id"] || (this[attr] || {}).id;

      if (object_id)
        this.attr(attr, CMS.Models.get_instance(
              model_name
            , object_id
            , this[attr]
            ).stub() || this[attr]);
    }

  , init_join_objects: function() {
      var that = this
        ;

      can.each(this.constructor.join_keys, function(model, attr) {
        if (model === can.Model.Cacheable)
          that.init_join_object_with_type(attr);
        else
          that.init_join_object(attr, model.shortName);
      });
    }
});

can.Model.Join("CMS.Models.Relationship", {
    root_object: "relationship"
  , root_collection: "relationships"
  , attributes : {
      context : "CMS.Models.Context.stub"
    , modified_by : "CMS.Models.Person.stub"
    , source : "CMS.Models.get_stub"
    , destination : "CMS.Models.get_stub"
  }
  , join_keys : {
    source : can.Model.Cacheable
    , destination : can.Model.Cacheable
  }
  , defaults : {
      source : null
    , destination : null
  }
  , findAll: "GET /api/relationships"
  , create: "POST /api/relationships"
  , destroy: "DELETE /api/relationships/{id}"
}, {
  reinit: function() {
    var that = this;

    this.attr("source", CMS.Models.get_instance(
      this.source_type
        || (this.source
            && (this.source.constructor
                && this.source.constructor.shortName
                || (!this.source.selfLink && this.source.type)))
      , this.source_id || (this.source && this.source.id)
      , this.source) || this.source);
    this.attr("destination", CMS.Models.get_instance(
      this.destination_type
        || (this.destination
            && (this.destination.constructor
                && this.destination.constructor.shortName
                || (!this.source.selfLink && this.destination.type)))
      , this.destination_id || (this.destination && this.destination.id)
      , this.destination) || this.destination);
  }
});

can.Model.Join("CMS.Models.ObjectSection", {
    root_object: "object_section"
  , root_collection: "object_sections"
  , join_keys : {
      "section" : CMS.Models.SectionBase
    , "sectionable" : can.Model.Cacheable
  }
  , attributes : {
      context : "CMS.Models.Context.stub"
    , modified_by : "CMS.Models.Person.stub"
    , section : "CMS.Models.get_stub"
    , sectionable : "CMS.Models.get_stub"
  }
  , findAll: "GET /api/object_sections"
  , create: "POST /api/object_sections"
  , destroy: "DELETE /api/object_sections/{id}"
}, {
});

can.Model.Join("CMS.Models.ObjectControl", {
    root_object: "object_control"
  , root_collection: "object_controls"
  , join_keys : {
      "control" : CMS.Models.Control
    , "controllable" : can.Model.Cacheable
  }
  , attributes : {
      context : "CMS.Models.Context.stub"
    , modified_by : "CMS.Models.Person.stub"
    , control : "CMS.Models.Control.stub"
    , controllable : "CMS.Models.get_stub"
  }
  , findAll: "GET /api/object_controls"
  , create: "POST /api/object_controls"
  , destroy: "DELETE /api/object_controls/{id}"
}, {
});

can.Model.Join("CMS.Models.ObjectObjective", {
    root_object: "object_objective"
  , root_collection: "object_objectives"
  , join_keys : {
      "objective" : CMS.Models.Objective
    , "objectiveable" : can.Model.Cacheable
  }
  , attributes : {
      context : "CMS.Models.Context.stub"
    , modified_by : "CMS.Models.Person.stub"
    , objective : "CMS.Models.Objective.stub"
    , objectiveable : "CMS.Models.get_stub"
  }
  , findAll: "GET /api/object_objectives"
  , create: "POST /api/object_objectives"
  , destroy: "DELETE /api/object_objectives/{id}"
}, {
});

can.Model.Join("CMS.Models.ProgramDirective", {
  root_object : "program_directive"
  , root_collection : "program_directives"
  , join_keys : {
      program : CMS.Models.Program
    , directive : CMS.Models.Directive
  }
  , attributes : {
      context : "CMS.Models.Context.stub"
    , modified_by : "CMS.Models.Person.stub"
    , program : "CMS.Models.Program.stub"
    , directive : "CMS.Models.get_stub"
  }
  , findAll: "GET /api/program_directives"
  , create: "POST /api/program_directives"
  , destroy : "DELETE /api/program_directives/{id}"
}, {
});

can.Model.Join("CMS.Models.ObjectiveControl", {
  root_object : "objective_control"
  , root_collection : "objective_controls"
  , attributes : {
      context : "CMS.Models.Context.stub"
    , modified_by : "CMS.Models.Person.stub"
    , objective : "CMS.Models.Objective.stub"
    , control : "CMS.Models.Control.stub"
    }
  , join_keys : {
      "objective" : CMS.Models.Objective
    , "control" : CMS.Models.Control
    }
  , findAll: "GET /api/objective_controls"
  , create: "POST /api/objective_controls"
  , destroy : "DELETE /api/objective_controls/{id}"
}, {
});

can.Model.Join("CMS.Models.UserRole", {
  root_object : "user_role"
  , root_collection : "user_roles"
  , findAll : "GET /api/user_roles"
  , update : "PUT /api/user_roles/{id}"
  , create : "POST /api/user_roles"
  , destroy : "DELETE /api/user_roles/{id}"
  , attributes : {
      context : "CMS.Models.Context.stub"
    , modified_by : "CMS.Models.Person.stub"
    , person : "CMS.Models.Person.stub"
    , role : "CMS.Models.Role.stub"
  }
  , join_keys : {
      person : CMS.Models.Person
    , role : CMS.Models.Role
  }
}, {
  save: function() {
    var roles,
        that = this
        _super =  this._super;
    if(!this.role && this.role_name) {
      roles = can.map(
        CMS.Models.Role.cache,
        function(role) { if(role.name === this.role_name) return role; }
      );
      if(roles.length > 0) {
        this.attr("roles", roles[0].stub());
        return _super.apply(this, arguments);
      } else {
        return CMS.Models.Role.findAll({ name__in : this.role_name }).then(function(roles) {
          if(roles.length < 1) {
            return new $.Deferred().reject("Role not found");
          }
          that.attr("role", roles[0].stub());
          return _super.apply(that, arguments);
        });
      }
    } else {
      return _super.apply(this, arguments);
    }
  }
});


can.Model.Join("CMS.Models.ControlSection", {
  root_collection : "control_sections"
  , root_object : "control_section"
  , findAll : "GET /api/control_sections"
  , create : "POST /api/control_sections"
  , destroy : "DELETE /api/control_sections/{id}"
  , join_keys : {
      section : CMS.Models.SectionBase
    , control : CMS.Models.Control
  }
  , attributes : {
      context : "CMS.Models.Context.stub"
    , modified_by : "CMS.Models.Person.stub"
    , section : "CMS.Models.get_stub"
    , control : "CMS.Models.Control.stub"
  }
}, {
});

can.Model.Join("CMS.Models.SectionObjective", {
  root_collection : "section_objectives"
  , root_object : "section_objective"
  , findAll : "GET /api/section_objectives"
  , create : "POST /api/section_objectives"
  , destroy : "DELETE /api/section_objectives/{id}"
  , join_keys : {
      section : CMS.Models.SectionBase
    , objective : CMS.Models.Objective
  }
  , attributes : {
      context : "CMS.Models.Context.stub"
    , modified_by : "CMS.Models.Person.stub"
    , section : "CMS.Models.get_stub"
    , objective : "CMS.Models.Objective.stub"
  }
}, {
});

can.Model.Join("CMS.Models.DirectiveControl", {
    root_collection : "directive_controls"
  , root_object : "directive_control"
  , findAll : "GET /api/directive_controls"
  , create : "POST /api/directive_controls"
  , destroy : "DELETE /api/directive_controls/{id}"
  , join_keys : {
      directive : CMS.Models.Directive
    , control : CMS.Models.Control
  }
  , attributes : {
      context : "CMS.Models.Context.stub"
    , modified_by : "CMS.Models.Person.stub"
    , directive : "CMS.Models.Directive.stub"
    , control : "CMS.Models.Control.stub"
  }
}, {
});

can.Model.Join("CMS.Models.DirectiveSection", {
    root_collection : "directive_sections"
  , root_object : "directive_section"
  , findAll : "GET /api/directive_sections"
  , create : "POST /api/directive_sections"
  , destroy : "DELETE /api/directive_sections/{id}"
  , join_keys : {
      directive : CMS.Models.Directive
    , section : CMS.Models.SectionBase
  }
  , attributes : {
      context : "CMS.Models.Context.stub"
    , modified_by : "CMS.Models.Person.stub"
    , directive : "CMS.Models.Directive.stub"
    , section : "CMS.Models.get_stub"
  }
}, {
});

can.Model.Join("CMS.Models.ProgramControl", {
  root_collection : "program_controls"
  , root_object : "program_control"
  , join_keys : {
      program : CMS.Models.Program
    , control : CMS.Models.Control
  }
  , attributes : {
      context : "CMS.Models.Context.stub"
    , modified_by : "CMS.Models.Person.stub"
    , program : "CMS.Models.Program.stub"
    , control : "CMS.Models.Control.stub"
  }
  , findAll : "GET /api/program_controls"
  , create : "POST /api/program_controls"
  , destroy : "DELETE /api/program_controls/{id}"
}, {

});

can.Model.Join("CMS.Models.ControlControl", {
  root_collection : "control_controls"
  , root_object : "control_control"
  , join_keys : {
      control : CMS.Models.Control
    , implemented_control : CMS.Models.Control
  }
  , attributes : {
      context : "CMS.Models.Context.stub"
    , modified_by : "CMS.Models.Person.stub"
    , control : "CMS.Models.Control.stub"
    , implemented_control : "CMS.Models.Control.stub"
  }
  , findAll : "GET /api/control_controls"
  , create : "POST /api/control_controls"
  , destroy : "DELETE /api/control_controls/{id}"
}, {

});

can.Model.Join("CMS.Models.ObjectPerson", {
  root_object : "object_person"
  , root_collection : "object_people"
  , findAll: "GET /api/object_people"
  , create : "POST /api/object_people"
  , update : "PUT /api/object_people/{id}"
  , destroy : "DELETE /api/object_people/{id}"
  , join_keys : {
    personable : can.Model.Cacheable
    , person : CMS.Models.Person
  }
  , attributes : {
      context : "CMS.Models.Context.stub"
    , modified_by : "CMS.Models.Person.stub"
    , person : "CMS.Models.Person.stub"
    , personable : "CMS.Models.get_stub"
  }

}, {});

can.Model.Join("CMS.Models.ObjectDocument", {
  root_object : "object_document"
  , root_collection : "object_documents"
  , findAll: "GET /api/object_documents"
  , create: "POST /api/object_documents"
  , destroy : "DELETE /api/object_documents/{id}"
  , join_keys : {
    documentable : can.Model.Cacheable
    , document : CMS.Models.Document
  }
  , attributes : {
      context : "CMS.Models.Context.stub"
    , modified_by : "CMS.Models.Person.stub"
    , document : "CMS.Models.Document.stub"
    , documentable : "CMS.Models.get_stub"
  }
}, {});

can.Model.Join("CMS.Models.MultitypeSearchJoin", {
  join_keys: {}
}, {});

can.Model.Join("CMS.Models.AuditObject", {
  root_object : "audit_object",
  root_collection : "audit_objects",
  findAll: "GET /api/audit_objects",
  create: "POST /api/audit_objects",
  destroy : "DELETE /api/audit_objects/{id}",
  join_keys : {
    auditable : can.Model.Cacheable,
    audit : CMS.Models.Audit
  },
  attributes : {
    context : "CMS.Models.Context.stub",
    modified_by : "CMS.Models.Person.stub",
    audit : "CMS.Models.Audit.stub",
    auditable : "CMS.Models.get_stub"
  }
}, {});

})(this.can, this.can.$);
