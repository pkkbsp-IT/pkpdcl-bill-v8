    def upsert_consumer(self, consumer, old_bp_id=None):
        consumers = self.data.setdefault("consumers", [])
        target_bp = str(old_bp_id or consumer.get("bp_id") or "").strip()
        new_bp = str(consumer.get("bp_id") or "").strip()

        clean_consumer = {
            "name": str(consumer.get("name") or "").strip(),
            "bp_id": new_bp,
            "mobile": str(consumer.get("mobile") or "").strip(),
            "meter": str(consumer.get("meter") or "").strip(),
            "address": str(consumer.get("address") or "").strip(),
            "rate": float(consumer.get("rate") or 8.30),
            "upi": str(consumer.get("upi") or "9009203060@ptsbi").strip(),
        }

        updated = False
        for idx, item in enumerate(consumers):
            item_bp = str(item.get("bp_id") or "").strip()
            if target_bp and item_bp == target_bp:
                consumers[idx] = clean_consumer
                updated = True
                break

        if not updated:
            consumers.append(clean_consumer)

        if old_bp_id and new_bp and str(old_bp_id).strip() != new_bp:
            for row in self.data.get("ledger", []):
                if str(row.get("bp_id") or "").strip() == str(old_bp_id).strip():
                    row["bp_id"] = new_bp

        self.save()
        return clean_consumer
