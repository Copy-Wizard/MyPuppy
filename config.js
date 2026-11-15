// MyPuppy site settings. Fill these in during setup (see README.md).
// The anon key is safe to publish: the database rules only let each user read and change their own row.
window.MYPUPPY_CONFIG = {
  supabaseUrl: "https://uirjizztbzorkxychwfb.supabase.co",       // e.g. "https://abcdefgh.supabase.co"
  supabaseAnonKey: "sb_publishable_tVIoh9mA7cX8ZNTCjdnnlA_zW8bcx73",   // Supabase > Project Settings > API > "anon public" key
  gumroad: {
    pass: "https://noumanibad.gumroad.com/l/mypuppy",            // Gumroad product link for the 90-Day Pass, e.g. "https://yourname.gumroad.com/l/mypuppy"
    lifetime: "",        // optional
    monthly: ""          // optional
  }
};
