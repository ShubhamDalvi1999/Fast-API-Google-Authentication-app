// Test Supabase Configuration
// Run this in browser console to test Supabase setup

import { createClient } from '@supabase/supabase-js';

const supabaseUrl = 'https://yaefwshrnbrkzugwfgra.supabase.co';
const supabaseAnonKey = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InlhZWZ3c2hybmJya3p1Z3dmZ3JhIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTU2MzgwODAsImV4cCI6MjA3MTIxNDA4MH0.8aXJwgeSQjDuffKt7nBw7nKzp4MvTh1o2SZr85cnwqM';

const supabase = createClient(supabaseUrl, supabaseAnonKey);

// Test OAuth URL generation
async function testSupabaseOAuth() {
  try {
    console.log('Testing Supabase OAuth...');
    
    const { data, error } = await supabase.auth.signInWithOAuth({
      provider: 'google',
      options: {
        redirectTo: 'http://localhost:3000/auth/supabase/callback'
      }
    });
    
    if (error) {
      console.error('Supabase OAuth error:', error);
      return;
    }
    
    console.log('Supabase OAuth data:', data);
    console.log('OAuth URL:', data.url);
    
    // Check if the URL contains the correct redirect
    if (data.url && data.url.includes('redirect_uri=http%3A%2F%2Flocalhost%3A3000%2Fauth%2Fsupabase%2Fcallback')) {
      console.log('✅ Redirect URL is correctly encoded in OAuth URL');
    } else {
      console.log('❌ Redirect URL is NOT correctly encoded in OAuth URL');
      console.log('Expected: redirect_uri=http%3A%2F%2Flocalhost%3A3000%2Fauth%2Fsupabase%2Fcallback');
      console.log('Actual URL:', data.url);
    }
    
  } catch (err) {
    console.error('Test failed:', err);
  }
}

// Run the test
testSupabaseOAuth();
