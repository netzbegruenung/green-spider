import _ from 'lodash';
import $ from 'jquery';
import 'bootstrap';
import 'popper.js';
import punycode from 'punycode';
import 'datatables.net';
import LazyLoad from 'vanilla-lazyload';

$(function(){

  var trunc = function(s, length) {
    if (s.length > length) {
      s = s.substring(0, length) + '…';
    }
    return s;
  };

  var table = null;

  $.getJSON('data/screenshots.json', function(screenshots){

    $.getJSON('data/spider_result.json', function(data){
      var tbody = $('tbody');
      $.each(data, function(index, item) {

        var row = $(document.createElement('tr'));

        // typ
        var level = null;
        if (item.meta.level === 'DE:ORTSVERBAND') {
          level = 'OV';
        } else if (item.meta.level === 'DE:KREISVERBAND') {
          level = 'KV';
        } else if (item.meta.level === 'DE:LANDESVERBAND') {
          level = 'LV';
        }
        row.append('<td>' + (level === null ? '' : level) + '</td>');

        // land
        row.append('<td>' + (item.meta.state === null ? '' : item.meta.state) + '</td>');

        // kreis
        row.append('<td>' + (item.meta.district === null ? '' : item.meta.district) + '</td>');

        // stadt
        row.append('<td>' + (item.meta.city === null ? '' : item.meta.city) + '</td>');

        // input URL
        row.append('<td><a href="' + item.input_url + '">' + trunc(punycode.toUnicode(item.input_url), 60) + '</a></td>');

        // score
        row.append('<td>' + item.score.toFixed(1) + '</td>');

        // IPs
        var ips = _.join(item.details.ipv4_addresses, ', ');
        row.append('<td class="text '+ (ips === '' ? 'bad' : 'good') +' text-center">' + (ips === '' ? '❌' : ips) + '</td>');

        // SITE_REACHABLE
        row.append('<td class="'+ (item.result.SITE_REACHABLE.value ? 'good' : 'bad') +' text-center">' + (item.result.SITE_REACHABLE.value ? '✅' : '❌') + '</td>');

        // HTTP_RESPONSE_DURATION
        var durationClass = 'bad';
        if (item.result.HTTP_RESPONSE_DURATION.score > 0) { durationClass = 'medium'; }
        if (item.result.HTTP_RESPONSE_DURATION.score > 0.5) { durationClass = 'good'; }
        row.append('<td class="text '+ durationClass +' text-center" data-order="' + item.result.HTTP_RESPONSE_DURATION.value + '">' + item.result.HTTP_RESPONSE_DURATION.value + ' ms</td>');

        // FAVICON
        var icon = item.result.FAVICON.value;
        row.append('<td class="' + (icon ? 'good' : 'bad') + ' text-center">' + (icon ? ('<img src="' + item.details.icons[0] + '" class="icon">') : '❌') + '</td>');

        // HTTPS
        var hasHTTPS = item.result.HTTPS.value;
        row.append('<td class="'+ (hasHTTPS ? 'good' : 'bad') +' text-center">' + (hasHTTPS ? '✅' : '❌') + '</td>');

        // WWW_OPTIONAL
        var wwwOptional = item.result.WWW_OPTIONAL.value;
        row.append('<td class="'+ (wwwOptional ? 'good' : 'bad') +' text-center">' + (wwwOptional ? '✅' : '❌') + '</td>');

        // one canonical URL
        var canonical = item.result.CANONICAL_URL.value;
        row.append('<td class="'+ (canonical ? 'good' : 'bad') +' text-center">' + (canonical ? '✅' : '❌') + '</td>');

        var responsive = item.result.RESPONSIVE.value;
        row.append('<td class="'+ (responsive ? 'good' : 'bad') +' text-center">' + (responsive ? '✅' : '❌') + '</td>');

        // feeds
        var feeds = item.result.FEEDS.value;
        row.append('<td class="'+ (feeds ? 'good' : 'bad') +' text-center">' + (feeds ? '✅' : '❌') + '</td>');

        // screenshots
        var screenshot = false;
        if (item.details.canonical_urls.length > 0) {
          if (typeof screenshots[item.details.canonical_urls[0]] !== 'undefined') {
            var surl = 'http://green-spider-screenshots.sendung.de/320x640/'+screenshots[item.details.canonical_urls[0]];
            var lurl = 'http://green-spider-screenshots.sendung.de/1500x1500/'+screenshots[item.details.canonical_urls[0]];
            screenshot = '<a class="screenshot" href="'+ surl +'" target="_blank" title="Mobile">M</a>';
            screenshot += '<a class="screenshot" href="'+ lurl +'" target="_blank" title="Desktop">D</a>';
          }
        }
        row.append('<td class="'+ (screenshot ? 'good' : 'bad') +' text-center">' + (screenshot ? screenshot : '❌') + '</td>');

        // cms
        row.append('<td class="text text-center">' + (item.details.cms ? item.details.cms : '') + '</td>');

        tbody.append(row);
      });

      // enable data table funcionts (sorting)
      table = $('table.table').DataTable({
        order: [[0, "asc"]],
        paging: false,
        pageLength: 10000,
        language: {
          "search": "Suche"
        }
      });

    });

  });

});
