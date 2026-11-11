"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";
import { Badge } from "@/components/ui/badge";
import { submitVendor, getSamples } from "@/lib/api";
import type { SampleCase, DocumentInfo } from "@/lib/types";

const EMPTY_DOC: DocumentInfo = { filename: "", document_type: "", content_summary: "" };

const initialForm = {
  company_name: "",
  trading_name: "",
  country: "",
  address: "",
  tax_id: "",
  contact_name: "",
  contact_email: "",
  bank_account_holder: "",
  iban: "",
  swift_bic: "",
  documents: [
    { ...EMPTY_DOC, document_type: "certificate_of_incorporation" },
    { ...EMPTY_DOC, document_type: "tax_registration" },
  ] as DocumentInfo[],
};

export default function SubmitPage() {
  const router = useRouter();
  const [form, setForm] = useState(initialForm);
  const [samples, setSamples] = useState<SampleCase[]>([]);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    getSamples().then(setSamples).catch(console.error);
  }, []);

  function loadSample(sample: SampleCase) {
    setForm({ ...sample.data });
  }

  function setField(key: string, value: string) {
    setForm((prev) => ({ ...prev, [key]: value }));
  }

  function setDoc(index: number, field: keyof DocumentInfo, value: string) {
    setForm((prev) => {
      const docs = [...prev.documents];
      docs[index] = { ...docs[index], [field]: value };
      return { ...prev, documents: docs };
    });
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    try {
      const result = await submitVendor(form);
      if (result.run_id) {
        router.push(`/run/${result.run_id}`);
      }
    } catch (err) {
      console.error(err);
      setSubmitting(false);
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold tracking-tight">New Vendor Submission</h2>
        <p className="text-muted-foreground">Submit vendor details for automated verification</p>
      </div>

      {samples.length > 0 && (
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm">Load Sample Data</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-2">
              {samples.map((s) => (
                <Button
                  key={s.key}
                  variant="outline"
                  size="sm"
                  onClick={() => loadSample(s)}
                  title={s.description}
                >
                  {s.label}
                </Button>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      <form onSubmit={handleSubmit} className="space-y-6">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Company Information</CardTitle>
          </CardHeader>
          <CardContent className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label>Company Name *</Label>
              <Input value={form.company_name} onChange={(e) => setField("company_name", e.target.value)} required />
            </div>
            <div className="space-y-2">
              <Label>Trading Name</Label>
              <Input value={form.trading_name} onChange={(e) => setField("trading_name", e.target.value)} />
            </div>
            <div className="space-y-2">
              <Label>Country Code *</Label>
              <Input value={form.country} onChange={(e) => setField("country", e.target.value.toUpperCase())} placeholder="e.g. DE, US, IN, GB" maxLength={2} required />
            </div>
            <div className="space-y-2">
              <Label>Tax ID *</Label>
              <Input value={form.tax_id} onChange={(e) => setField("tax_id", e.target.value)} required />
            </div>
            <div className="col-span-2 space-y-2">
              <Label>Address *</Label>
              <Input value={form.address} onChange={(e) => setField("address", e.target.value)} required />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">Contact Information</CardTitle>
          </CardHeader>
          <CardContent className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label>Contact Name *</Label>
              <Input value={form.contact_name} onChange={(e) => setField("contact_name", e.target.value)} required />
            </div>
            <div className="space-y-2">
              <Label>Contact Email *</Label>
              <Input type="email" value={form.contact_email} onChange={(e) => setField("contact_email", e.target.value)} required />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">Banking Information</CardTitle>
          </CardHeader>
          <CardContent className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label>Bank Account Holder *</Label>
              <Input value={form.bank_account_holder} onChange={(e) => setField("bank_account_holder", e.target.value)} required />
            </div>
            <div className="space-y-2">
              <Label>IBAN / Account Number *</Label>
              <Input value={form.iban} onChange={(e) => setField("iban", e.target.value)} required />
            </div>
            <div className="space-y-2">
              <Label>SWIFT/BIC Code</Label>
              <Input value={form.swift_bic} onChange={(e) => setField("swift_bic", e.target.value)} />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">Documents</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {form.documents.map((doc, i) => (
              <div key={i} className="space-y-3 p-4 rounded-md border">
                <div className="flex items-center gap-2">
                  <Badge variant="outline">Document {i + 1}</Badge>
                  <span className="text-xs text-muted-foreground">{doc.document_type.replace(/_/g, " ")}</span>
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <div className="space-y-1">
                    <Label className="text-xs">Filename</Label>
                    <Input value={doc.filename} onChange={(e) => setDoc(i, "filename", e.target.value)} placeholder="e.g. certificate.pdf" />
                  </div>
                  <div className="space-y-1">
                    <Label className="text-xs">Document Type</Label>
                    <Input value={doc.document_type} onChange={(e) => setDoc(i, "document_type", e.target.value)} />
                  </div>
                </div>
                <div className="space-y-1">
                  <Label className="text-xs">Content Summary</Label>
                  <Input value={doc.content_summary} onChange={(e) => setDoc(i, "content_summary", e.target.value)} placeholder="Brief description of the document contents" />
                </div>
              </div>
            ))}
          </CardContent>
        </Card>

        <Separator />

        <div className="flex justify-end">
          <Button type="submit" size="lg" disabled={submitting}>
            {submitting ? "Submitting..." : "Submit for Verification"}
          </Button>
        </div>
      </form>
    </div>
  );
}
