/**
 * Web Intern Platform - Google Apps Script Webhook
 * Auto-creates tabs: Registrations, Applications, Certificates, and All Events Log
 */

function doPost(e) {
  try {
    var data = JSON.parse(e.postData.contents);
    var eventType = data.event || "UNKNOWN";
    var payload = data.data || {};
    var ss = SpreadsheetApp.getActiveSpreadsheet();

    // 1. Always log raw event to "All Events Log"
    logEvent(ss, eventType, payload);

    // 2. Dispatch to specific sheet tab based on event type
    if (eventType === "REGISTER") {
      handleRegistration(ss, payload);
    } else if (eventType === "APPLICATION") {
      handleApplication(ss, payload);
    } else if (eventType === "CERTIFICATE") {
      handleCertificate(ss, payload);
    }

    return ContentService.createTextOutput(JSON.stringify({
      status: "success",
      event: eventType,
      message: "Event logged successfully to Google Sheets"
    })).setMimeType(ContentService.MimeType.JSON);

  } catch (error) {
    return ContentService.createTextOutput(JSON.stringify({
      status: "error",
      message: error.toString()
    })).setMimeType(ContentService.MimeType.JSON);
  }
}

function doGet(e) {
  return ContentService.createTextOutput(JSON.stringify({
    status: "online",
    service: "Web Intern Google Sheets Webhook"
  })).setMimeType(ContentService.MimeType.JSON);
}

function handleRegistration(ss, d) {
  var sheet = getOrCreateSheet(ss, "Registrations", [
    "Timestamp", "User ID", "Full Name", "Email", "Phone", "College", "Department", "Degree"
  ]);
  sheet.appendRow([
    new Date(),
    d.user_id || d.id || "",
    d.full_name || "",
    d.email || "",
    d.phone || "",
    d.college || "",
    d.department || "",
    d.degree || ""
  ]);
}

function handleApplication(ss, d) {
  var sheet = getOrCreateSheet(ss, "Applications", [
    "Timestamp", "Application ID", "Student Name", "Email", "Internship Title", "Offer Letter ID", "Start Date", "End Date", "Status"
  ]);
  sheet.appendRow([
    new Date(),
    d.application_id || d.id || "",
    d.student_name || d.full_name || "",
    d.email || "",
    d.internship_title || "",
    d.offer_letter_id || "",
    d.start_date || "",
    d.end_date || "",
    d.status || "active"
  ]);
}

function handleCertificate(ss, d) {
  var sheet = getOrCreateSheet(ss, "Certificates", [
    "Timestamp", "Certificate ID", "Student Name", "Email", "Internship Title", "Offer Letter ID", "Payment Status", "Certificate URL", "Issued At"
  ]);
  sheet.appendRow([
    new Date(),
    d.certificate_id || d.id || "",
    d.student_name || "",
    d.email || "",
    d.internship_title || "",
    d.offer_letter_id || "",
    d.is_verified_paid ? "VERIFIED & PAID" : "PENDING",
    d.certificate_url || "",
    d.issued_at || new Date()
  ]);
}

function logEvent(ss, eventType, payload) {
  var sheet = getOrCreateSheet(ss, "All Events Log", ["Timestamp", "Event Type", "Payload JSON"]);
  sheet.appendRow([new Date(), eventType, JSON.stringify(payload)]);
}

function getOrCreateSheet(ss, name, headers) {
  var sheet = ss.getSheetByName(name);
  if (!sheet) {
    sheet = ss.insertSheet(name);
    if (headers && headers.length > 0) {
      sheet.appendRow(headers);
      var range = sheet.getRange(1, 1, 1, headers.length);
      range.setFontWeight("bold");
      range.setBackground("#1e293b");
      range.setFontColor("#ffffff");
    }
  }
  return sheet;
}
