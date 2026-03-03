import 'package:flutter_test/flutter_test.dart';
import 'package:samsun_mobil_app/services/api_service.dart';

// ApiService'in veri parse mantığını test eden birim testleri.
// Bu testler gerçek API çağrısı yapmaz, sadece veri işleme fonksiyonlarını doğrular.

void main() {
  group('ApiService._extractDataList', () {
    // _extractDataList private olduğu için, parse fonksiyonlarını
    // farklı ASIS yanıt formatları ile test ediyoruz.

    test('_parseRealTimeData: düz liste formatını doğru parse eder', () {
      // Proxy yanıtı: doğrudan liste
      final proxyData = [
        {'enlem': 41.29, 'boylam': 36.33, 'plaka': '55 AA 001', 'hiz': 35, 'HatKodu': 'R1'},
        {'enlem': 41.30, 'boylam': 36.34, 'plaka': '55 AA 002', 'hiz': 20, 'HatKodu': 'R1'},
      ];

      final result = ApiService.parseRealTimeDataForTest(proxyData, 'R1');
      expect(result.length, 2);
      expect(result[0]['lat'], 41.29);
      expect(result[0]['lon'], 36.33);
      expect(result[0]['plate'], '55 AA 001');
      expect(result[0]['speed'], '35');
      expect(result[0]['lineCode'], 'R1');
    });

    test('_parseRealTimeData: Samsun dışı koordinatları filtreler', () {
      final data = [
        {'enlem': 41.29, 'boylam': 36.33, 'plaka': '55 AA 001', 'hiz': 35}, // Geçerli
        {'enlem': 39.00, 'boylam': 32.00, 'plaka': '06 XX 999', 'hiz': 50}, // Ankara, geçersiz
        {'enlem': 0.0, 'boylam': 0.0, 'plaka': 'UNKNOWN', 'hiz': 0},       // Sıfır, geçersiz
      ];

      final result = ApiService.parseRealTimeDataForTest(data, 'TEST');
      expect(result.length, 1);
      expect(result[0]['plate'], '55 AA 001');
    });

    test('_parseRealTimeData: string koordinatları doğru parse eder', () {
      // ASIS bazen string döner
      final data = [
        {'enlem': '41.2900', 'boylam': '36.3300', 'plaka': '55 BB 003', 'hiz': '45'},
      ];

      final result = ApiService.parseRealTimeDataForTest(data, 'R2');
      expect(result.length, 1);
      expect(result[0]['lat'], closeTo(41.29, 0.001));
      expect(result[0]['lon'], closeTo(36.33, 0.001));
    });

    test('_cleanSmartStationData: BusLineCode filtreler ve düzeltir', () {
      final data = [
        {'BusLineCode': 'R1 - SAMSUN', 'RemainingTimeCurr': 5},
        {'BusLineCode': 'OTOPARK YÖNETIM', 'RemainingTimeCurr': 10}, // skipKeyword
        {'BusLineCode': 'R2 - ATAKUM', 'RemainingTimeCurr': 8},
        {'NoCode': 'invalid'}, // BusLineCode yok
      ];

      final result = ApiService.cleanSmartStationDataForTest(data);
      expect(result.length, 2);
      expect(result[0]['BusLineCode'], 'R1 - SAMSUN');
      expect(result[1]['BusLineCode'], 'R2 - ATAKUM');
    });

    test('_cleanSmartStationData: Türkçe karakter düzeltme', () {
      final data = [
        {'BusLineCode': 'SAMULA\u015e - TRAMVAY', 'RemainingTimeCurr': 3},
      ];

      final result = ApiService.cleanSmartStationDataForTest(data);
      expect(result.length, 1);
    });

    test('extractDataList: {"data": [...]} formatını çıkarır', () {
      final wrappedResponse = {
        'data': [
          {'enlem': 41.29, 'boylam': 36.33, 'plaka': '55 CC 001'},
          {'enlem': 41.30, 'boylam': 36.34, 'plaka': '55 CC 002'},
        ]
      };

      final result = ApiService.extractDataListForTest(wrappedResponse);
      expect(result.length, 2);
      expect(result[0]['plaka'], '55 CC 001');
    });

    test('extractDataList: düz listeyi olduğu gibi döner', () {
      final listResponse = [
        {'enlem': 41.29, 'boylam': 36.33, 'plaka': '55 DD 001'},
      ];

      final result = ApiService.extractDataListForTest(listResponse);
      expect(result.length, 1);
    });

    test('extractDataList: tekil objeyi listeye sarar', () {
      final singleResponse = {'enlem': 41.29, 'boylam': 36.33, 'plaka': '55 EE 001'};

      final result = ApiService.extractDataListForTest(singleResponse);
      expect(result.length, 1);
      expect(result[0]['plaka'], '55 EE 001');
    });
  });

  group('Türkçe Karakter Düzeltme', () {
    test('Bozuk Türkçe karakterleri düzeltir', () {
      final text = ApiService.fixAndCleanTextForTest('SAM\u00deULA\u00de');
      // Þ→Ş mapping'i ile
      expect(text.contains('Ş'), isTrue);
    });
  });
}
