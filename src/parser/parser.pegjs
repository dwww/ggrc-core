/*
    Copyright (C) 2013 Google Inc., authors, and contributors <see AUTHORS file>
    Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
    Created By: miha@reciprocitylabs.com
    Maintained By: miha@reciprocitylabs.com
*/


start
  = _* only_order_by:only_order_by _*
    {
      return {
        expression: {},
        keys: [],
        order_by: only_order_by,
        evaluate: function(values) {
          // functions evaluates the current expresion tree, with the given values
          //
          // * values, Object with all the keys as in the this keys array, 
          //   with the coresponding values
          return true;
        }
      };
    }
  / _* or_exp:or_exp order_by:order_by _*
    {
      var keys = jQuery.unique(or_exp.keys.sort());
      delete or_exp.keys;
      return {
        expression: or_exp,
        keys: keys,
        order_by: order_by,
        evaluate: function(values) {
          // functions evaluates the current expresion tree, with the given values
          //
          // * values, Object with all the keys as in the this keys array, 
          //   with the coresponding values
          try {
            return or_exp.evaluate(values);
          } catch (e) {
            return false;
          }
        }
      };
    }
  / _* 
    {
      return {
        expression: {},
        keys: [],
        order_by: { 
          keys: [], 
          order: '',
          compare: null
        },
        evaluate: function(values) {
          return true;
        }
      };
    }
  / .* 
    {
      return false;
    }

order_by
  = ' ' only_order_by:only_order_by
    {
      return only_order_by;
    }
  / _*
    {
      return { 
        keys: [], 
        order: '',
        compare: null
      };
    }

only_order_by
  = _* 'order by'i _+ word_list:word_list order:order
    {
      return { 
        keys: word_list, 
        order: order,
        compare: function(val1, val2){
          for (var i in word_list){
            var key = word_list[i];
            if (val1._data[key] !== val2._data[key]){
              var a = parseFloat(val1._data[key]) || val1._data[key],
                  b = parseFloat(val2._data[key]) || val2._data[key];
              return (a < b) ^ (order !== 'asc')
            }
          }
          return false;
        }
      };
    }

word_list
  = word:word ',' word_list:word_list
    {
      return [word].concat(word_list);
    }

  / word:word
    {
      return [word];
    }
 
order
  = _+ 'desc'i _*
    {
      return 'desc';
    }
  / _+ 'asc'i _*
    {
      return 'asc';
    }
  / _*
    {
      return 'asc';
    }


or_exp
  = left:and_exp op:OR right:or_exp
    {
      var keys = left.keys.concat(right.keys);
      delete right.keys;
      delete left.keys;
      return {
        left: left,
        op: op,
        right: right,
        keys: keys,
        evaluate: function(values) {
          return op.evaluate(left.evaluate(values), right.evaluate(values));
        }
      };
    }
  / and_exp


and_exp
  = left:simple_exp op:AND right:and_exp
    {
      var keys = left.keys.concat(right.keys);
      delete right.keys;
      delete left.keys;
      return {
        left:left,
        op: op,
        right: right,
        keys: keys,
        evaluate: function(values) {
          return op.evaluate(left.evaluate(values), right.evaluate(values));
        }
      };
    }
  / simple_exp


simple_exp
  = left:word op:OP right:word
    {
      return {
        left:left,
        op: op,
        right: right,
        keys: [left],
        evaluate: function(values){
          return op.evaluate(values[left], right);
        }
      };
    }
  / paren_exp
  / text_exp

text_exp
  = _* "~" characters:.*
    {
      return {
        text: characters.join("").trim(),
        op: 'text_search',
        keys: [],
        evaluate: function(values){
          for (var i in values){
            if (values[i].toUpperCase().indexOf(this.text.toUpperCase()) > -1 ){
              return true;
            }
          }
          return false;
        }
      };
    }

paren_exp 
  = LEFT_P or_exp:or_exp RIGHT_P
    {
      return or_exp;
    }


word
  = unquoted_word
  / quoted_word


unquoted_word
  = word:unqoted_char+
    {
      return word.join('');
    }


quoted_word
  = '"' word:quoted_char* '"'
    {
      return word.join('');
    }

unqoted_char = [a-zA-Z0-9_\-.]


quoted_char
  = '\\"' 
    { 
      return '"'; 
    }
  / [^"]


AND
  = _+ 'AND'i _+
    {
      return {name: 'AND', evaluate: function(val1, val2) { return val1 && val2; } };
    }
  / _* '&&'   _*
    {
      return {name: 'AND', evaluate: function(val1, val2) { return val1 && val2; } };
    }


OR
  = _+ 'OR'i  _+
    {
      return {name: 'OR', evaluate: function(val1, val2) { return val1 || val2;} };
    }
  / _* '||'   _*
    {
      return {name: 'OR', evaluate: function(val1, val2) { return val1 || val2; } };
    }


OP
  = _* op:'=' _*
    {
      return {
        name: op,
        evaluate: function(val1, val2) {
          return val1 == val2;
        }
      };
    }
  / _* op:'!=' _*
    {
      return {
        name: op,
        evaluate: function(val1, val2) {
          return val1 != val2;
        }
      };
    }
  / _* op:'<' _*
    {
      return {
        name: op,
        evaluate: function(val1, val2) {
          return val1 < val2;
        }
      };
    }
  / _* op:'>' _*
    {
      return {
        name: op,
        evaluate: function(val1, val2) {
          return val1 > val2;
        }
      };
    }
  / _* op:'~' _*
    {
      return {
        name: op,
        evaluate: function(val1, val2) {
          return val1.toUpperCase().indexOf(val2.toUpperCase()) > -1 ;
        }
      };
    }
  / _* op:'!~' _*
    {
      return {
        name: op,
        evaluate: function(val1, val2) {
          return val1.toUpperCase().indexOf(val2.toUpperCase()) == -1 ;
        }
      };
    }


LEFT_P = '(' _*

RIGHT_P = _* ')'

_ = [ \t\r\n\f]+



