import 'package:flutter/material.dart';

class AlarmScreen extends StatefulWidget {
  final Map<String, dynamic> durak;

  const AlarmScreen({Key? key, required this.durak}) : super(key: key);

  @override
  State<AlarmScreen> createState() => _AlarmScreenState();
}

class _AlarmScreenState extends State<AlarmScreen> {
  TimeOfDay selectedTime = TimeOfDay.now();
  String selectedHat = "R2"; // Örnek
  int alertMinutesBefore = 5;

  Future<void> _selectTime(BuildContext context) async {
    final TimeOfDay? picked = await showTimePicker(
      context: context,
      initialTime: selectedTime,
    );
    if (picked != null && picked != selectedTime) {
      setState(() {
        selectedTime = picked;
      });
    }
  }

  void _saveAlarm() {
    // Burada aslında Local Notification veya WorkManager ile arka plan görevi kurulur
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text("⏰ Akıllı Hazırlanma Alarmı Kuruldu!\nHer gün ${selectedTime.format(context)}'da ${widget.durak['ad']} durağı için $selectedHat hattı $alertMinutesBefore dk kala uyarı verecek."),
        backgroundColor: Colors.green,
      ),
    );
    Navigator.pop(context);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text("Akıllı Hazırlanma Alarmı"),
        backgroundColor: Colors.redAccent,
      ),
      body: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              "Hedef Durak:\n${widget.durak['ad']}",
              style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 20),
            ListTile(
              title: const Text("Her Gün Bu Saatte Uyar:"),
              trailing: Text(
                selectedTime.format(context),
                style: const TextStyle(fontSize: 22, color: Colors.blue, fontWeight: FontWeight.bold),
              ),
              onTap: () => _selectTime(context),
              tileColor: Colors.grey.withOpacity(0.1),
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
            ),
            const SizedBox(height: 20),
            ListTile(
              title: const Text("Beklenen Hat (Örn: R2, E1):"),
              trailing: SizedBox(
                width: 100,
                child: TextField(
                  onChanged: (val) => selectedHat = val,
                  decoration: const InputDecoration(hintText: "Örn: R2"),
                ),
              ),
            ),
            const SizedBox(height: 20),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                const Text("Otobüs gelmeden kaç dk önce uyarılıyım?", style: TextStyle(fontSize: 16)),
                DropdownButton<int>(
                  value: alertMinutesBefore,
                  items: [3, 5, 10, 15].map((int value) {
                    return DropdownMenuItem<int>(
                      value: value,
                      child: Text("$value dk"),
                    );
                  }).toList(),
                  onChanged: (val) {
                    setState(() {
                      alertMinutesBefore = val!;
                    });
                  },
                ),
              ],
            ),
            const Spacer(),
            SizedBox(
              width: double.infinity,
              height: 50,
              child: ElevatedButton.icon(
                onPressed: _saveAlarm,
                icon: const Icon(Icons.alarm_on),
                label: const Text("PROAKTİF ALARMI KAYDET", style: TextStyle(fontSize: 18)),
                style: ElevatedButton.styleFrom(
                  backgroundColor: Colors.redAccent,
                  foregroundColor: Colors.white,
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(15)),
                ),
              ),
            ),
            const SizedBox(height: 20),
          ],
        ),
      ),
    );
  }
}
