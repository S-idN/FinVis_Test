// settings_page.dart
import 'package:flutter/material.dart';

class SettingsPage extends StatelessWidget {
  const SettingsPage({Key? key}) : super(key: key);

  // User Agreement Text
  final String _userAgreementText = """
  **User Agreement**

  Welcome to FinvisionAI. By using our application, you agree to the following terms and conditions:

  **1. Terms of Service**
  - You must be at least 18 years old to use this application.
  - You agree to use the application only for lawful purposes.

  **2. Privacy Policy**
  - We collect and use your personal data to provide and improve our services.
  - Your data will be handled in accordance with our Privacy Policy.

  **3. Intellectual Property**
  - All content provided by FinvisionAI is protected by copyright laws.

  **4. Disclaimer**
  - FinvisionAI is not liable for any damages arising from the use of this application.

  **5. Termination**
  - We reserve the right to terminate or suspend your access to the application at any time.

  By continuing to use FinvisionAI, you acknowledge that you have read, understood, and agree to be bound by these terms and conditions.
  """;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text("Settings"),
        backgroundColor: const Color(0xFF00359E), // Dark blue color
        titleTextStyle: const TextStyle(
          color: Colors.white,
          fontSize: 20,
          fontWeight: FontWeight.bold,
        ),
      ),
      body: Padding(
        padding: const EdgeInsets.all(16.0),
        child: ListView(
          children: [
            // User Agreement
            ListTile(
              title: const Text('User Agreement'),
              subtitle: const Text('More on licensing'),
              leading: const Icon(Icons.lock),
              onTap: () {
                _showUserAgreement(context);
              },
            ),
            // Add more settings options as needed
          ],
        ),
      ),
    );
  }

  void _showUserAgreement(BuildContext context) {
    showDialog(
      context: context,
      builder: (BuildContext context) {
        return AlertDialog(
          title: const Text("User Agreement"),
          content: SingleChildScrollView(
            child: ListBody(
              children: [
                Text(
                  _userAgreementText,
                  style: TextStyle(fontSize: 14),
                ),
              ],
            ),
          ),
          actions: <Widget>[
            TextButton(
              child: const Text('Close'),
              onPressed: () {
                Navigator.of(context).pop();
              },
            ),
          ],
        );
      },
    );
  }
}