from flask import Flask, request
from pydantic import BaseModel

app = Flask(__name__)
@app.route("/bill/split/v1", methods=["GET"])
def split_bill() -> dict:
    #Get the bill
    body = request.get_json(force=True)
    # app.logger.warning(body)
    #get the discount
    discount = body["discount"]
    #validate the discount
    assert discount <= 1.0, "Discount cannot be greater than 1.0"
    final_bill = {}
    payers = set()
    for item in body["items"]:
        #validate each item
        assert "name" in item, "Item name is required"
        assert "can_discount" in item, "Item discount validation flag is required"
        assert "assigned_to" in item, "Item assigned to is required"
        assert "price" in item, "Item price is required"
        #make sure item has only 4 keys
        assert len(item.keys())==4, "Item can only have name, can_discount, assigned_to, price"
        price = item["price"]
        #calculate the subtotal before discount
        final_bill["subtotal"] = final_bill.get("subtotal", 0) + price
        if item["can_discount"]:
            price = price - (price*discount)
        #calculate the subtotal after discount
        final_bill["subtotal_after_discount"] = final_bill.get("subtotal_after_discount", 0) + price
        #calculate the split price equally among assigned to people
        split_price = price/len(item["assigned_to"])
        for payer in item["assigned_to"]:
            #make sure payer is not subtotal or subtotal_after_discount or total
            assert payer != "subtotal", "Payer cannot be subtotal"
            assert payer != "subtotal_after_discount", "Payer cannot be subtotal_after_discount"
            assert payer != "total"
            payers.add(payer)
            #add the split price to payer
            final_bill[payer] = final_bill.get(payer, 0) + split_price
    for payer in payers:
        #calculate the tax and tip ratio for each payer
        tax_tip_ratio = final_bill[payer]/final_bill["subtotal_after_discount"]
        final_bill[payer] = final_bill[payer] + ((body["tax"]+body["tip"])*tax_tip_ratio)
        app.logger.warning(final_bill)
    #calculate the total bill
    final_bill["total"] = final_bill["subtotal_after_discount"] + body["tip"] + body["tax"]
    #round the bill to 2 decimal places
    for key in final_bill.keys():
        final_bill[key] = round(final_bill[key], 2)
    return(final_bill)
