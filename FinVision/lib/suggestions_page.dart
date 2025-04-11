// suggestions_page.dart
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'package:google_fonts/google_fonts.dart';

class SuggestionsPage extends StatefulWidget {
  const SuggestionsPage({super.key});
  @override
  _SuggestionsPageState createState() => _SuggestionsPageState();
}

class _SuggestionsPageState extends State<SuggestionsPage> {
  String suggestions = "Fetching suggestions...";
  List<Map<String, String>> productAlternatives = [];

  Future<void> fetchSuggestions() async {
    const url = "http://192.168.1.41:8012/get_suggestions/"; // Replace with actual IP
    try {
      final response = await http.post(
        Uri.parse(url),
        headers: {"Content-Type": "application/json"},
        body: jsonEncode({"expense_data": "Your expense details here"}),
      );
      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        setState(() {
          suggestions = data['suggestions'] ?? "No suggestions available.";
          productAlternatives = List<Map<String, String>>.from(data['product_alternatives'] ?? []);
        });
      } else {
        setState(() {
          suggestions = "Error: ${response.statusCode} - ${response.body}";
        });
      }
    } catch (e) {
      setState(() {
        suggestions = "Network Error: Failed to fetch suggestions.";
      });
    }
  }

  @override
  void initState() {
    super.initState();
    fetchSuggestions();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text("Suggestions"),
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
            // Suggestions Text
            Text(
              suggestions,
              textAlign: TextAlign.center,
              style: GoogleFonts.roboto(
                fontSize: 18,
                fontWeight: FontWeight.w500,
              ),
            ),
            const SizedBox(height: 20),

            // Product Alternatives
            if (productAlternatives.isNotEmpty)
              Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text(
                    "Product Alternatives",
                    style: TextStyle(
                      fontSize: 18,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  const SizedBox(height: 10),
                  ListView.builder(
                    shrinkWrap: true,
                    physics: const NeverScrollableScrollPhysics(),
                    itemCount: productAlternatives.length,
                    itemBuilder: (context, index) {
                      final product = productAlternatives[index]['product'] ?? "Unknown Product";
                      final price = productAlternatives[index]['price'] ?? "Unknown Price";
                      return Card(
                        elevation: 4,
                        margin: const EdgeInsets.symmetric(vertical: 5),
                        child: Padding(
                          padding: const EdgeInsets.all(16.0),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                product,
                                style: const TextStyle(
                                  fontSize: 16,
                                  fontWeight: FontWeight.bold,
                                ),
                              ),
                              const SizedBox(height: 5),
                              Text(
                                "Price: \$${price}",
                                style: const TextStyle(
                                  fontSize: 14,
                                ),
                              ),
                            ],
                          ),
                        ),
                      );
                    },
                  ),
                ],
              )
            else
              const Center(
                child: Text("No product alternatives available."),
              ),
          ],
        ),
      ),
    );
  }
}