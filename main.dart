import 'package:flutter/material.dart';

void main() {
  runApp(const TeamManagementApp());
}

class TeamManagementApp extends StatelessWidget {
  const TeamManagementApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Team Attendance & Scores',
      rtlUnconstrainedFrame: true,
      theme: ThemeData(
        primarySwatch: Colors.blue,
        fontFamily: 'Tajawal',
      ),
      home: const HomeScreen(),
    );
  }
}

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  int _score = 10;
  
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('نظام إدارة الفريق التفاعلي'),
        centerTitle: true,
      ),
      body: Center(
        child: Column(
          mainAxisAlignment: MainCenter,
          children: [
            const Icon(Icons.qr_code_scanner, size: 80, color: Colors.blue),
            const SizedBox(height: 20),
            Text(
              'الدرجة الحالية للحاضر: $_score / 10',
              style: const TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 20),
            ElevatedButton(
              onPressed: () {
                // فتح الكاميرا لمسح الـ Barcode
              },
              child: const Text('مسح الباركود عبر الكاميرا'),
            )
          ],
        ),
      ),
    );
  }
}
