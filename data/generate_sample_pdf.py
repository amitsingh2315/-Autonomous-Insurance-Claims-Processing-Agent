"""
Generate a sample ACORD-style FNOL (First Notice of Loss) PDF for testing.

This creates a realistic automobile loss notice document with structured data
that the extraction pipeline can process.

Usage:
    python data/generate_sample_pdf.py
"""

from fpdf import FPDF
import os


def generate_sample_fnol():
    """Generate a sample ACORD Automobile Loss Notice PDF."""
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # --- Header ---
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "ACORD AUTOMOBILE LOSS NOTICE", ln=True, align="C")
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 6, "FIRST NOTICE OF LOSS (FNOL)", ln=True, align="C")
    pdf.ln(8)

    # --- Horizontal line ---
    pdf.set_draw_color(0, 0, 0)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(5)

    # --- Policy Information ---
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "POLICY INFORMATION", ln=True)
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 6, "Policy Number: AUTO-2024-78432", ln=True)
    pdf.cell(0, 6, "Policyholder Name: Robert James Mitchell", ln=True)
    pdf.cell(0, 6, "Policy Effective Date: 01/15/2024 to 01/15/2025", ln=True)
    pdf.cell(0, 6, "Insurance Company: National Auto Insurance Corp", ln=True)
    pdf.cell(0, 6, "Agent Name: Sarah Williams", ln=True)
    pdf.cell(0, 6, "Agent Phone: (555) 234-5678", ln=True)
    pdf.ln(5)

    # --- Incident Information ---
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "INCIDENT / ACCIDENT DETAILS", ln=True)
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 6, "Date of Loss: 03/15/2024", ln=True)
    pdf.cell(0, 6, "Time of Loss: 14:35", ln=True)
    pdf.cell(0, 6, "Location: Intersection of Main St and Oak Ave, Springfield, IL 62701", ln=True)
    pdf.ln(3)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 6, "Description of Accident:", ln=True)
    pdf.set_font("Helvetica", "", 10)
    pdf.multi_cell(0, 5,
        "The insured vehicle was traveling northbound on Main Street at approximately "
        "35 mph when a third-party vehicle ran a red light at the intersection of Oak Avenue "
        "and collided with the insured vehicle on the driver side. The impact caused significant "
        "damage to the driver side door and front fender. The insured driver applied brakes but "
        "was unable to avoid the collision. Weather conditions were clear and the road surface was dry. "
        "Police report was filed (Report #SPD-2024-04521)."
    )
    pdf.ln(5)

    # --- Involved Parties ---
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "INVOLVED PARTIES", ln=True)

    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 6, "Claimant / Insured Driver:", ln=True)
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 6, "Name: Robert James Mitchell", ln=True)
    pdf.cell(0, 6, "Phone: (555) 987-6543", ln=True)
    pdf.cell(0, 6, "Email: r.mitchell@email.com", ln=True)
    pdf.cell(0, 6, "Address: 1234 Elm Street, Springfield, IL 62704", ln=True)
    pdf.cell(0, 6, "Driver License: IL-D1234567", ln=True)
    pdf.ln(3)

    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 6, "Third Party:", ln=True)
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 6, "Name: Jennifer L. Thompson", ln=True)
    pdf.cell(0, 6, "Phone: (555) 321-0987", ln=True)
    pdf.cell(0, 6, "Insurance: State Farm Policy #SF-8876543", ln=True)
    pdf.cell(0, 6, "Vehicle: 2021 Honda Civic, Silver, Plate: IL-ABC1234", ln=True)
    pdf.ln(5)

    # --- Vehicle / Asset Details ---
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "VEHICLE / ASSET DETAILS", ln=True)
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 6, "Asset Type: Vehicle", ln=True)
    pdf.cell(0, 6, "Year/Make/Model: 2022 Toyota Camry SE", ln=True)
    pdf.cell(0, 6, "VIN: 4T1G11AK5NU000123", ln=True)
    pdf.cell(0, 6, "License Plate: IL-XYZ7890", ln=True)
    pdf.cell(0, 6, "Color: Midnight Blue", ln=True)
    pdf.cell(0, 6, "Mileage at Loss: 28,450 miles", ln=True)
    pdf.ln(3)

    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 6, "Damage Description:", ln=True)
    pdf.set_font("Helvetica", "", 10)
    pdf.multi_cell(0, 5,
        "Driver side door crushed inward, front left fender bent, side mirror broken, "
        "driver side window shattered. Airbag deployed. Vehicle is drivable but with "
        "significant body damage."
    )
    pdf.cell(0, 6, "Estimated Damage: $18,500", ln=True)
    pdf.ln(5)

    # --- Claim Information ---
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "CLAIM INFORMATION", ln=True)
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 6, "Claim Type: Collision", ln=True)
    pdf.cell(0, 6, "Initial Estimate: $18,500", ln=True)
    pdf.cell(0, 6, "Deductible: $500", ln=True)
    pdf.cell(0, 6, "Injuries Reported: None", ln=True)
    pdf.cell(0, 6, "Tow Required: No", ln=True)
    pdf.cell(0, 6, "Rental Car Needed: Yes", ln=True)
    pdf.ln(3)

    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 6, "Attachments:", ln=True)
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 6, "1. Police Report (SPD-2024-04521)", ln=True)
    pdf.cell(0, 6, "2. Photos of vehicle damage (4 images)", ln=True)
    pdf.cell(0, 6, "3. Repair estimate from ABC Auto Body", ln=True)
    pdf.ln(5)

    # --- Witness Information ---
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "WITNESS INFORMATION", ln=True)
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 6, "Witness: Mark Davis, Phone: (555) 456-7890", ln=True)
    pdf.cell(0, 6, "Witness statement: Confirmed third-party vehicle ran red light.", ln=True)
    pdf.ln(5)

    # --- Signature ---
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(5)
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 6, "Report Filed By: Robert James Mitchell", ln=True)
    pdf.cell(0, 6, "Date Filed: 03/15/2024", ln=True)
    pdf.cell(0, 6, "Signature: [Electronically Signed]", ln=True)

    # --- Save ---
    output_dir = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(output_dir, "sample_fnol.pdf")
    pdf.output(output_path)
    print(f"[OK] Sample FNOL PDF generated: {output_path}")
    return output_path


if __name__ == "__main__":
    generate_sample_fnol()
