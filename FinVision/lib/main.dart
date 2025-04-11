import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'media_selection_page.dart'; // Import the ExpenseScanner as MediaSelectionPage
import 'settings_page.dart'; // Import the SettingsPage
import 'insights_page.dart'; // Assuming we'll move the insights page to a separate file
import 'suggestions_page.dart';

void main() {
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      title: 'FinvisionAI',
      theme: ThemeData(
        useMaterial3: true, // Enable Material 3 (Cashew-like)
        colorScheme: ColorScheme.fromSeed(
          seedColor: const Color(0xFF00359E), // Cashew-like Blue
        ),
        textTheme: GoogleFonts.robotoTextTheme(), // Modern font
        appBarTheme: const AppBarTheme(
          backgroundColor: Color(0xFF00359E), // Dark blue
          titleTextStyle: TextStyle(
            color: Colors.white,
            fontSize: 20,
            fontWeight: FontWeight.bold,
          ),
          iconTheme: IconThemeData(color: Colors.white),
        ),
      ),
      initialRoute: '/',
      routes: {
        '/': (context) => const MediaSelectionPage(),
        '/settings': (context) => const SettingsPage(),
        '/suggestions': (context) => const SuggestionsPage(),
        //'/insights': (context) => const InsightsPage(), // Add the new route// Add the new route
      },
    );
  }
}

// For the media_selection_page.dart file:
/*
Make sure to extract the ExpenseScannerPage from the previous code and save it
as media_selection_page.dart with the appropriate class name changes.
*/

// For the insights_page.dart file:
/*
Extract the InsightsPage from the previous code and save it as insights_page.dart
*/

// For the settings_page.dart file:
/*
Make sure you have a proper implementation for the SettingsPage
*/