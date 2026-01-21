import database

print("Checking Sheet Headers...")
try:
    # Access the sheet object from database module
    if database.sheet:
        headers = database.sheet.row_values(1)
        print(f"Current Headers: {headers}")
        
        required = ["Date", "Item", "Amount", "Category", "Remarks"]
        missing = [h for h in required if h not in headers]
        
        if missing:
            print(f"❌ MISSING HEADERS: {missing}")
            print("Fixing headers...")
            # Insert headers at row 1 if missing
            # But wait, if there is data in row 1, we should insert_row, not overwrite?
            # Or maybe row 1 is data?
            
            if not headers:
                # Empty sheet
                database.sheet.append_row(required)
                print("✅ Headers added to empty sheet.")
            else:
                # Sheet has data but maybe meant to be headers?
                # If first row looks like a date '2026-...', it's data.
                if headers[0][0].isdigit(): # Simple heuristic
                    print("⚠️ First row looks like data, inserting headers above it.")
                    database.sheet.insert_row(required, index=1)
                    print("✅ Headers inserted.")
                else:
                    print("⚠️ Headers might be named differently or just missing some?")
        else:
            print("✅ Headers look correct.")
            
    else:
        print("❌ Database sheet object is None.")
except Exception as e:
    print(f"❌ Error checking headers: {e}")
