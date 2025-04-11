import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert'; // For jsonEncode and jsonDecode
import 'dart:async'; // For TimeoutException
import 'package:google_fonts/google_fonts.dart';
import 'package:flutter/foundation.dart'; // Import for debugPrint

class InsightsPage extends StatefulWidget {
  const InsightsPage({super.key});

  @override
  _InsightsPageState createState() => _InsightsPageState();
}

class _InsightsPageState extends State<InsightsPage> {
  String insights = "Initial State Value"; // Change initial value for clarity

  @override
  void initState() {
    super.initState();
    // Use debugPrint for potentially better visibility in some consoles
    debugPrint("--- initState: CALLED ---");
    fetchInsights();
    debugPrint("--- initState: fetchInsights() Called ---");
  }

  Future<void> fetchInsights() async {
    // ---- Start of Function Marker ----
    debugPrint("--- fetchInsights: Function ENTERED ---");

    const url = "http://192.168.1.7:8012/analyze-finances"; //change this IP to computer/local IP

    // ---- Before setState Marker ----
    debugPrint("--- fetchInsights: About to call setState (mounted: $mounted) ---");
    if (mounted) {
      setState(() {
        insights = "Fetching analysis...";
      });
      debugPrint("--- fetchInsights: setState COMPLETED ---");
    } else {
      debugPrint("--- fetchInsights: setState SKIPPED (unmounted) ---");
    }

    // ---- Before Try Block Marker ----
    debugPrint("--- fetchInsights: Entering TRY block ---");
    try {
      debugPrint("--- fetchInsights: Attempting POST request to: $url ---"); // Critical Checkpoint 1

      final response = await http.post(
        Uri.parse(url),
        headers: {"Content-Type": "application/json"},
        body: jsonEncode({
          // ... (your JSON body remains the same)
          "income": 7500.00,
          "expenses": {
            "Rent": 2000.00, "Utilities": 150.50, "Groceries": 700.00,
            "Transport": 250.00, "Insurance": 120.00, "Phone Bill": 80.00,
            "Subscriptions": 45.00
          },
          "savings_goals": {
            "Emergency Fund": 10000.00, "Vacation": 3000.00, "New Laptop": 1500.00
          },
          "discretionary_percentage": 0.15,
        }),
      ).timeout(const Duration(seconds: 20));

      // ---- After HTTP Call Marker ----
      debugPrint("--- fetchInsights: http.post FINISHED (status: ${response.statusCode}) ---"); // Critical Checkpoint 2
      debugPrint("--- fetchInsights: Response body: ${response.body} ---");

      if (!mounted) {
        debugPrint("--- fetchInsights: Widget unmounted after request, exiting. ---");
        return; // Exit if widget is gone
      }

      if (response.statusCode == 200) {
        debugPrint("--- fetchInsights: Status is 200, decoding JSON... ---");
        final decodedResponse = jsonDecode(response.body);
        final analysisText = decodedResponse['analysis'] as String?;
        debugPrint("--- fetchInsights: Decoded analysis text: $analysisText ---");

        if (analysisText != null && analysisText.isNotEmpty) {
          debugPrint("--- fetchInsights: Setting state to SUCCESS data ---");
          setState(() {
            insights = analysisText;
          });
        } else {
          debugPrint("--- fetchInsights: Setting state to ERROR (null/empty analysis) ---");
          setState(() {
            insights = "Error: Received empty or invalid analysis data from server.\nResponse: ${response.body}";
          });
        }
      } else {
        debugPrint("--- fetchInsights: Setting state to ERROR (status code ${response.statusCode}) ---");
        setState(() {
          insights = "Error fetching analysis: ${response.statusCode}\n${response.body}";
        });
      }

    } on TimeoutException catch (e, s) {
      debugPrint("--- fetchInsights: CAUGHT TimeoutException ---");
      debugPrint("Error: $e");
      debugPrint("Stack: $s");
      if (mounted) {
        setState(() {
          insights = "Error: The request timed out. Server might be busy, slow, or unreachable at $url.";
        });
      }
    } on http.ClientException catch (e, s) {
      debugPrint("--- fetchInsights: CAUGHT ClientException (Network Error) ---");
      debugPrint("Error: $e");
      debugPrint("Stack: $s");
      if (mounted) {
        setState(() {
          insights = "Network Error: Failed to connect to the server. Is it running at $url?\nDetails: $e";
        });
      }
    } on FormatException catch (e, s) {
      debugPrint("--- fetchInsights: CAUGHT FormatException (JSON Error) ---");
      debugPrint("Error: $e");
      debugPrint("Stack: $s");
      if (mounted) {
        setState(() {
          insights = "Error: Could not parse the server response (Invalid JSON).\nDetails: $e";
        });
      }
    } catch (e, s) {
      debugPrint("--- fetchInsights: CAUGHT UNEXPECTED ERROR ---");
      debugPrint("Error: $e");
      debugPrint("Stack: $s");
      if (mounted) {
        setState(() {
          insights = "An unexpected error occurred: $e";
        });
      }
    } finally {
      debugPrint("--- fetchInsights: Function EXITED (Finally Block) ---");
    }
  }

  @override
  Widget build(BuildContext context) {
    debugPrint("--- Build method CALLED. Current insights: '$insights' ---"); // See if build is triggered
    return Scaffold(
      appBar: AppBar( /* ... AppBar remains the same ... */
        title: const Text("Insights"),
        backgroundColor: const Color(0xFF00359E),
        titleTextStyle: const TextStyle(
          color: Colors.white,
          fontSize: 20,
          fontWeight: FontWeight.bold,
        ),
        iconTheme: const IconThemeData(color: Colors.white),
      ),
      body: Padding(
        padding: const EdgeInsets.all(16.0),
        child: ListView(
          children: [
            Card( /* ... Card remains the same ... */
              elevation: 4,
              margin: const EdgeInsets.symmetric(vertical: 10),
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(8.0),
              ),
              child: Padding(
                padding: const EdgeInsets.all(16.0),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text(
                      "Financial Analysis",
                      style: TextStyle(
                        fontSize: 18,
                        fontWeight: FontWeight.bold,
                        color: Color(0xFF00359E),
                      ),
                    ),
                    const SizedBox(height: 15),
                    SelectableText(
                      insights, // Displays state value
                      style: GoogleFonts.roboto(
                        fontSize: 15,
                        height: 1.4,
                        color: Colors.black87,
                      ),
                      textAlign: TextAlign.justify,
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 20),
            Center(
              child: ElevatedButton.icon(
                onPressed: () {
                  // Add print statement directly in onPressed
                  debugPrint("--- Refresh Button PRESSED ---");
                  fetchInsights(); // Call the fetch function again
                },
                icon: const Icon(Icons.refresh),
                label: const Text("Refresh Analysis"),
                style: ElevatedButton.styleFrom(
                  backgroundColor: const Color(0xFF00359E), // Button background
                  foregroundColor: Colors.white, // Text and icon color
                  padding: const EdgeInsets.symmetric(
                    horizontal: 24,
                    vertical: 12,
                  ),
                  textStyle: const TextStyle(
                    fontSize: 16,
                    fontWeight: FontWeight.bold,
                  ),
                  shape: RoundedRectangleBorder( // Rounded corners for button
                    borderRadius: BorderRadius.circular(8.0),
                  ),
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