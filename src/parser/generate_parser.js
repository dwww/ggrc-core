#!/usr/bin/env node
/*
    Copyright (C) 2013 Google Inc., authors, and contributors <see AUTHORS file>
    Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
    Created By: miha@reciprocitylabs.com
    Maintained By: miha@reciprocitylabs.com
*/

/*
Script used to generate ggrc_filter_query_parser.js 

-- updating dev enviroment by running: 

  vagrant provision 

-- manual dev env setup:

to run this script you need node.js and peg.js
  sudo apt-get install nodejs npm
  npm install pegjs
  npm install mkdirp

if npm install returns a 404 just run the next command and try again.
  npm config set registry http://registry.npmjs.org/


then edit the parser.pegjs file and run the generator
  ./generate_parser.js
 
to run the tests first install nodeunit
  npm install -g nodeunit

and run with the test folder
  nodeunit test
  
*/


var parser_grammar = '/vagrant/src/parser/parser.pegjs';
var parser_template_file = '/vagrant/src/parser/parser_template.js'; 
var ggrc_parser_folder = '/vagrant/src/ggrc/assets/javascripts/generated/';
var ggrc_parser_js_file = 'ggrc_filter_query_parser.js';

var peg = require('pegjs');
var fs = require('fs');
var mkdirp = require('mkdirp');
var parser_string = fs.readFileSync(parser_grammar, 'utf8');
var filter_template = fs.readFileSync(parser_template_file, 'utf8');


// dirty way of making the parser work in node.js without jquery
root.jQuery = {
  unique : function(k) {
    return Object.keys(k.reduce(function(o,v,i) {o[v] = true; return o;}, {}));
  }
}


console.log('building parser');
var parser = peg.buildParser(parser_string);
var parser_src = peg.buildParser(parser_string, {output: "source"});

console.log('saving parser to js files');
var ggrc_parser = filter_template.replace('GENERATED_PLACEHOLDER', parser_src);

mkdirp.sync(ggrc_parser_folder);
fs.writeFileSync(ggrc_parser_folder + ggrc_parser_js_file, ggrc_parser);

// some sanity checks:
// actual tests are located in src/ggrc/assets/js_specs/generated
console.log('\nsome sanity tests');
var p = parser.parse('a="b" and (c=d or dd=something && aoeu=dd)');
var pp = parser.parse('(a=b and c=d) or dd=something && aoeu=dd');

var vals = {a:'b', c:'d', dd:'something', aoeu:'dd', y:'neki'};
var vals2 = {a:'bb', c:'d', dd:'something', aoeu:'dd', y:'neki'};
var vals3 = {a:'bi', c:'d', dd:'something', aoeu:'dd', y:'neki'};
console.log('true  :', p.evaluate(vals));
console.log('false :', p.evaluate(vals2));
console.log('true  :', pp.evaluate(vals2));
console.log("true  :", parser.parse('~  b  ').evaluate(vals2))

console.log("exp: ", parser.parse('a = oueo order by a,b,"c c"'))
console.log("exp: ", parser.parse('~ order by  aaa'))

console.log('\ndone :)');
