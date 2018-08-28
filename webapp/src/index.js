import _ from 'lodash';
import $ from 'jquery';
import 'bootstrap';
import punycode from 'punycode';
import 'datatables.net';
import 'tooltipster';

$(function(){

  var trunc = function(s, length) {
    if (s.length > length) {
      s = s.substring(0, length) + '…';
    }
    return s;
  };

  var table = null;

  var yes = '<i class="icon ion-md-checkmark-circle"></i>',
    no = '<i class="icon ion-md-close-circle"></i>';

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
        } else if (item.meta.level === 'DE:REGIONALVERBAND') {
          level = 'RV';
        } else if (item.meta.level === 'DE:BEZIRKSVERBAND') {
          level = 'BV';
        } else if (item.meta.level === 'DE:LANDESVERBAND') {
          level = 'LV';
        }
        row.append('<td data-order="'+ (level === null ? '' : level) +'"><span class="tt" title="Art der Gliederung: LV = Landesverband, BV = Bezirksverband, RV = Regionalverband, KV = Kreisverband, OV = Ortsverband">' + (level === null ? '' : level) + '</span></td>');

        // land
        row.append('<td>' + (item.meta.state === null ? '' : item.meta.state) + '</td>');

        // kreis
        row.append('<td>' + (item.meta.district === null ? '' : item.meta.district) + '</td>');

        // stadt
        row.append('<td>' + (item.meta.city === null ? '' : item.meta.city) + '</td>');

        // input URL
        row.append('<td data-order="' + item.input_url + '"><span class="tt" title="URL, die als Ausgangspunkt für diese Site vorliegt. Nicht notwendigerweise die kanonische URL."><a href="' + item.input_url + '" target="_blank" rel="noopener noreferrer">' + trunc(punycode.toUnicode(item.input_url), 60) + '</a></span></td>');

        // score
        row.append('<td data-order="' + item.score.toFixed(3) + '"><span class="tt" title="Punktzahl für diese Site (je höher desto besser)">' + item.score.toFixed(1) + '</span></td>');

        // IPs
        var ips = _.join(item.details.ipv4_addresses, ', ');
        row.append('<td class="text '+ (ips === '' ? 'bad' : 'good') +' text-center" data-order="' + ips + '"><span class="tt" title="IPv4-Adresse(n) des Servers bzw. der Server">' + (ips === '' ? no : ips) + '</span></td>');
 
        // SITE_REACHABLE
        var reachable = '<span class="tt" title="Die Site war beim Check erreichbar.">' + yes + '</span>';
        if (!item.result.SITE_REACHABLE.value) {
          reachable = '<span class="tt" title="Die Site war beim Check nicht erreichbar.">' + no + '</span>';
        }
        row.append('<td class="'+ (item.result.SITE_REACHABLE.value ? 'good' : 'bad') +' text-center" data-order="'+ (item.result.SITE_REACHABLE.value ? '1' : '0') +'">' + reachable + '</td>');

        // HTTP_RESPONSE_DURATION
        if (!item.result.SITE_REACHABLE.value || item.result.HTTP_RESPONSE_DURATION.value === null) {
          row.append('<td class="text bad text-center" data-order="99999999"><span class="tt" title="Nicht anwendbar">' + no + '</span></td>');
        } else {
          var durationClass = 'bad';
          if (item.result.HTTP_RESPONSE_DURATION.score > 0) { durationClass = 'medium'; }
          if (item.result.HTTP_RESPONSE_DURATION.score > 0.5) { durationClass = 'good'; }
          row.append('<td class="text '+ durationClass +' text-center" data-order="' + item.result.HTTP_RESPONSE_DURATION.value + '"><span class="tt" title="Dauer, bis der Server die Seitenanfrage beantwortet. Unter 100 ms ist sehr gut. Unter 1 Sekunde ist okay.">' + item.result.HTTP_RESPONSE_DURATION.value + ' ms</span></td>');
        }

        // FAVICON
        var icon = item.result.FAVICON.value && (Object.keys(item.details.icons).length > 0);
        var iconFile = icon ? Object.values(item.details.icons)[0] : '';
        var noicon = '<span class="tt" title="Diese Site hat kein Icon.">'+ no +'</span>'
        var icontag = (icon ? ('<img src="/siteicons/' + iconFile + '" class="siteicon tt" title="Die Site verweist auf das gezeigte Icon.">') : noicon);
        row.append('<td class="' + (icon ? 'good' : 'bad') + ' text-center" data-order="'+ iconFile +'">' + icontag + '</td>');

        // HTTPS
        var hasHTTPS = item.result.HTTPS.value;
        var hasHTTPScontent = (hasHTTPS ? '<span class="tt" title="Die Site ist über HTTPS erreichbar">' + yes + '</span>' : '<span class="tt" title="Die Site ist nicht über HTTPS erreichbar (-2 Punkte).">' + no + '</span>')
        row.append('<td class="'+ (hasHTTPS ? 'good' : 'bad') +' text-center" data-order="'+ (hasHTTPS ? '1' : '0') +'">' + hasHTTPScontent + '</td>');

        // WWW_OPTIONAL
        var wwwOptional = item.result.WWW_OPTIONAL.value;
        var wwwOptionalcontent = (wwwOptional ? '<span class="tt" title="Die Site ist sowohl mit als auch ohne www. in der URL aufrufbar">' + yes + '</span>' : '<span class="tt" title="Die Site ist nicht sowohl mit als auch ohne www. in der URL aufrufbar.">' + no + '</span>')
        row.append('<td class="'+ (wwwOptional ? 'good' : 'bad') +' text-center" data-order="'+ (wwwOptional ? '1' : '0') +'">' + wwwOptionalcontent + '</td>');

        // one canonical URL
        var canonical = item.result.CANONICAL_URL.value;
        var canonicalContent = (canonical ? '<span class="tt" title="Verschiedene URL-Varianten werden auf eine einzige umgeleitet">' + yes + '</span>' : '<span class="tt" title="Verschiedene URL-Varianten werden nicht auf eine einzige umgeleitet.">' + no + '</span>');
        row.append('<td class="'+ (canonical ? 'good' : 'bad') +' text-center" data-order="'+ (canonical ? '1' : '0') +'">' + canonicalContent + '</td>');

        var responsive = item.result.RESPONSIVE.value;
        var responsiveContent = (responsive ? '<span class="tt" title="Die Site funktioniert anscheinend auch auf mobilen Geräten">' + yes + '</span>' : '<span class="tt" title="Es scheint, als funktioniert die Site nicht auf mobilen Geräten.">' + no + '</span>');
        row.append('<td class="'+ (responsive ? 'good' : 'bad') +' text-center" data-order="'+ (responsive ? '1' : '0') +'">' + responsiveContent + '</td>');

        // feeds
        var feeds = item.result.FEEDS.value;
        var feedsContent = (feeds ? '<span class="tt" title="Die Site verweist auf mind. einen RSS-/Atom-Feed.">' + yes + '</span>' : '<span class="tt" title="Kein Link rel=alternate auf einen RSS-/Atom-Feed gefunden.">' + no + '</span>');
        row.append('<td class="'+ (feeds ? 'good' : 'bad') +' text-center" data-order="'+ (feeds ? '1' : '0') +'">' + feedsContent + '</td>');

        // screenshots
        var screenshot = false;
        if (item.details.canonical_urls && item.details.canonical_urls.length > 0) {
          if (typeof screenshots[item.details.canonical_urls[0]] !== 'undefined') {
            var surl = 'http://green-spider-screenshots.sendung.de/320x640/'+screenshots[item.details.canonical_urls[0]];
            var lurl = 'http://green-spider-screenshots.sendung.de/1500x1500/'+screenshots[item.details.canonical_urls[0]];
            screenshot = '<a class="screenshot tt" href="'+ surl +'" target="_blank" title="Screenshot für Smartphone-Ansicht anzeigen"><i class="icon ion-md-phone-portrait"></i></a>';
            screenshot += '<a class="screenshot tt" href="'+ lurl +'" target="_blank" title="Screenshot für Desktop-Ansicht anzeigen"><i class="icon ion-md-desktop"></i></a>';
          }
        }
        var noscreenshot = '<span class="tt" title="Für diese Site liegen aktuell keine Screenshots vor (führt nicht zu Punktabzug).">' + no + '</span>';
        row.append('<td class="'+ (screenshot ? 'good' : 'bad') +' text-center" data-order="'+ (screenshot ? '1' : '0') +'">' + (screenshot ? screenshot : noscreenshot) + '</td>');

        // cms
        row.append('<td class="text text-center">' + (item.details.cms ? item.details.cms : '') + '</td>');

        tbody.append(row);
      });

      // enable data table functions (sorting)
      table = $('table.table').DataTable({
        order: [[0, "asc"]],
        paging: false,
        pageLength: 10000,
        language: {
          "search": "Suche"
        }
      });

      // activate tooltips
      $('.tt').tooltipster({
        animationDuration: 100,
        theme: 'tooltipster-borderless'
      });

    });

  });

});
