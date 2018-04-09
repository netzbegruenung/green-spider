import _ from 'lodash';
import $ from 'jquery';
import 'bootstrap';
import 'popper.js';
import punycode from 'punycode';
import 'datatables.net';


$(function(){

  $.getJSON('data/spider_result.json', function(data){
    var tbody = $('tbody');
    $.each(data, function(index, item) {
      var row = $(document.createElement('tr'));

      // input URL
      row.append('<td><a href="' + item.input_url + '">' + punycode.toUnicode(item.input_url) + '</a></td>');

      // IPs
      var ips = _.join(_.uniq(_.flatten(_.map(item.hostnames, 'ip_addresses'))), ', ');
      row.append('<td class="'+ (ips === '' ? 'bad' : 'good') +' text-center">' + (ips === '' ? '❌  Keine' : ips) + '</td>');

      // icon
      var icons = [];
      var icon = false;
      icons = _.uniq(_.map(item.urlchecks, 'content.icon'));
      if (icons.length > 0 && icons[0]) {
        icon = icons[0];
      }
      row.append('<td class="' + (icon ? 'good' : 'bad') + ' text-center">' + (icon ? ('<img src="' + icon + '" class="icon"/>') : '❌') + '</td>');

      // hostnames
      var twoHostnames = false;
      if (_.filter(item.hostnames, {'resolvable': true}).length === 2) {
        twoHostnames = true;
      };
      row.append('<td class="'+ (twoHostnames ? 'good' : 'bad') +' text-center">' + (twoHostnames ? '✅' : '❌') + '</td>');

      // one canonical URL
      var canonical = false;
      if (item.canonical_urls.length === 1 ) canonical = true;
      var canonical_links = _.uniq(_.map(item.urlchecks, 'content.canonical_link'));
      if (canonical_links.length === 1) canonical = true;
      row.append('<td class="'+ (canonical ? 'good' : 'bad') +' text-center">' + (canonical ? '✅' : '❌') + '</td>');

      // https
      var hasHTTPS = false;
      hasHTTPS = _.find(item.canonical_urls, function(o){
        return o.indexOf('https://') !== -1;
      });
      row.append('<td class="'+ (hasHTTPS ? 'good' : 'bad') +' text-center">' + (hasHTTPS ? '✅' : '❌') + '</td>');

      // feeds
      var feeds = false;
      feeds = _.uniq(_.flatten(_.map(item.urlchecks, 'content.feeds')));
      row.append('<td class="'+ (feeds.length ? 'good' : 'bad') +' text-center">' + (feeds.length ? '✅' : '❌') + '</td>');

      tbody.append(row);
    });

    // enable data table funcionts (sorting)
    $('table.table').DataTable({
      order: [[0, "asc"]],
      paging: false,
      pageLength: 10000,
      language: {
        "search": "Suche"
      }
    });
  });

});
