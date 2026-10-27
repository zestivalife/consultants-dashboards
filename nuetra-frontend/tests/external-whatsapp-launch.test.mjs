import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

import {
  buildWhatsAppUrl,
  canonicaliseWhatsAppPhone,
  closeReservedWhatsAppWindow,
  navigateReservedWhatsAppWindow,
  normaliseWhatsAppPhone,
  reserveWhatsAppWindow,
} from "../lib/whatsappLaunch.mjs";

test("WhatsApp URLs use the client's digits and an encoded draft", () => {
  assert.equal(normaliseWhatsAppPhone("+91 (97620) 06688"), "919762006688");
  assert.equal(
    buildWhatsAppUrl({ phone: "+91 97620 06688", message: "Hello & welcome" }),
    "https://wa.me/919762006688?text=Hello%20%26%20welcome",
  );
  assert.equal(
    buildWhatsAppUrl({ message: "Choose a WhatsApp contact" }),
    "https://wa.me?text=Choose%20a%20WhatsApp%20contact",
  );
});

test("WhatsApp recipients use the client's selected country and remove local trunk prefixes", () => {
  assert.equal(canonicaliseWhatsAppPhone("09762006688", "IN"), "+919762006688");
  assert.equal(canonicaliseWhatsAppPhone("+91 97620 06688", "US"), "+919762006688");
  assert.equal(canonicaliseWhatsAppPhone("020 7946 0018", "GB"), "+442079460018");
  assert.equal(
    buildWhatsAppUrl({ phone: "09762006688", countryIso2: "IN", message: "Hello" }),
    "https://wa.me/919762006688?text=Hello",
  );
  assert.equal(
    buildWhatsAppUrl({ phone: "020 7946 0018", country_iso2: "GB" }),
    "https://wa.me/442079460018",
  );
});

test("a blank WhatsApp window is reserved synchronously and then navigated", () => {
  const calls = [];
  const popup = {
    closed: false,
    opener: "parent",
    location: { replace: (url) => calls.push(["replace", url]) },
    close: () => calls.push(["close"]),
  };
  const browserWindow = {
    open: (...args) => {
      calls.push(["open", ...args]);
      return popup;
    },
  };

  assert.equal(reserveWhatsAppWindow(browserWindow), popup);
  assert.equal(popup.opener, null);
  assert.deepEqual(calls[0], ["open", "about:blank", "_blank"]);

  const url = navigateReservedWhatsAppWindow(
    popup,
    { phone: "+91 90000 00000", message: "Your secure link" },
    browserWindow,
  );
  assert.equal(url, "https://wa.me/919000000000?text=Your%20secure%20link");
  assert.deepEqual(calls[1], ["replace", url]);

  closeReservedWhatsAppWindow(popup);
  assert.deepEqual(calls[2], ["close"]);
});

test("external share surfaces route through the shared WhatsApp launcher", async () => {
  const [api, assessment, calendar, invitation, client360, portal] = await Promise.all([
    readFile(new URL("../lib/practiceOperationsApi.js", import.meta.url), "utf8"),
    readFile(new URL("../components/external/ExternalNutritionAssessment.jsx", import.meta.url), "utf8"),
    readFile(new URL("../components/external/ExternalCalendarWorkspace.jsx", import.meta.url), "utf8"),
    readFile(new URL("../components/external/ExternalConsultantWorkspace.jsx", import.meta.url), "utf8"),
    readFile(new URL("../components/external/ExternalClient360.jsx", import.meta.url), "utf8"),
    readFile(new URL("../pages/client-portal/[token].js", import.meta.url), "utf8"),
  ]);

  assert.ok(api.indexOf("reserveWhatsAppWindow()") < api.indexOf("await request('/communication/whatsapp-opened'"));
  assert.match(api, /payload\.country_iso2\|\|payload\.countryIso2/);
  assert.match(assessment, /buildWhatsAppUrl\(\{phone:clientPhone,countryIso2:clientCountryIso2/);
  assert.match(assessment, /clientCountryIso2=\{clientCountryIso2\}/);
  assert.match(calendar, /Share via WhatsApp/);
  assert.match(invitation, /phone:client\.mobile/);
  assert.match(client360, /clientPhone=\{client\.mobile\|\|overview\?\.primaryContact/);
  assert.match(portal, /This is separate from WhatsApp/);
});
