// Receives Gumroad's "Ping" after each sale and unlocks the buyer's MyPuppy account.
// Ping URL to set in Gumroad: https://<project>.supabase.co/functions/v1/gumroad-ping?secret=<PING_SECRET>
import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

Deno.serve(async (req) => {
  const url = new URL(req.url);
  const secret = Deno.env.get("PING_SECRET");
  if (!secret || url.searchParams.get("secret") !== secret) return new Response("forbidden", { status: 403 });
  if (req.method !== "POST") return new Response("method not allowed", { status: 405 });

  const form = await req.formData();
  const email = String(form.get("email") ?? "").toLowerCase().trim();
  const saleId = String(form.get("sale_id") ?? "").trim();
  const product = String(form.get("product_permalink") ?? form.get("permalink") ?? form.get("product_name") ?? "");
  const refunded = String(form.get("refunded") ?? "false") === "true";
  const test = String(form.get("test") ?? "false") === "true";
  if (!email || !saleId) return new Response("missing email or sale_id", { status: 400 });

  const sb = createClient(Deno.env.get("SUPABASE_URL")!, Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!);
  const { error: e1 } = await sb.from("purchases").upsert({ sale_id: saleId, email, product, refunded });
  if (e1) { console.error(e1); return new Response("db error", { status: 500 }); }
  const { error: e2 } = await sb.from("profiles").update({ unlocked: !refunded, plan: product }).eq("email", email);
  if (e2) { console.error(e2); return new Response("db error", { status: 500 }); }
  console.log(`sale ${saleId} ${email} refunded=${refunded} test=${test}`);
  return new Response("ok");
});
