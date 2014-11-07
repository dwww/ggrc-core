/*
 * Copyright (C) 2013 Google Inc., authors, and contributors <see AUTHORS file>
 * Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
 * Created By: brad@reciprocitylabs.com
 * Maintained By: brad@reciprocitylabs.com
 */


(function(can, $) {

can.Control("GGRC.Controllers.PbcWorkflows", {

}, {

  "{CMS.Models.Audit} created" : function(model, ev, instance) {
    var that = this;
    
    if(instance instanceof CMS.Models.Audit) {
      if(instance.auto_generate) {
        instance.delay_resolving_save_until(
          instance.program.reify().refresh()
          .then(function(program) {
            return program.get_binding("controls").refresh_instances();
          }).then(function(control_mappings) {
            return can.reduce(control_mappings, function(deferred, control_mapping){
              return deferred.then(function(){
                return that.create_audit_object(instance, control_mapping.instance);
              }).then(function(audit_object) {
                return that.create_request(instance, audit_object);
              });
            }, $.when());
          })
        );
      }
    }
  }

  , create_objective : function(audit) {
    return new CMS.Models.Objective({
      title : "Generic request"
      , context : audit.context
      , contact : audit.contact || CMS.Models.Person.model(GGRC.current_user)
    }).save();
  }

  , map_objective_to_program : function(program, objective) {
    return new CMS.Models.ObjectObjective({
      objectiveable : program.stub()
      , objective : objective.stub()
      , context : objective.context
    }).save();
  }

  , create_audit_object: function(audit, control) {
    return new CMS.Models.AuditObject({
      audit: audit.stub(),
      auditable: control.stub(),
      context: audit.context
    }).save();
  }

  , create_request : function(audit, audit_object) {
    return new CMS.Models.Request({
      assignee : audit.contact || CMS.Models.Person.model(GGRC.current_user)
      , audit : audit.stub()
      , start_at : new Date()
      , end_at : moment().add(30, "days").toDate()
      , due_on : audit.stop_date || moment().add(30, "days").toDate()
      , audit_object : audit_object.stub()
      , request_type : "documentation"
      , description : "Please provide evidence of the type requested to demonstrate this Objective has been met."
      , context : audit.context
    }).save();
  }

  , update_objective_title : function(request) {
    var objective = request.objective.reify();
    objective.refresh().then(function() {
      objective.attr("title", objective.title + " " + request.attr("id")).save();
    });
    return request;
  }

  , create_response : function(request) {
    return new CMS.Models[request.response_model_class()]({
      pbc_response : "Generic response"
      , request : request.stub()
      , context : request.context
      , contact : request.assignee
    }).save();
  }

});

$(function() {
  $(document.body).ggrc_controllers_pbc_workflows();
});

})(this.can, this.can.$);
