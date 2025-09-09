// Direct Supabase OAuth service
import { createClient } from '@supabase/supabase-js'

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || 'https://yaefwshrnbrkzugwfgra.supabase.co'
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InlhZWZ3c2hybmJya3p1Z3dmZ3JhIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTU2MzgwODAsImV4cCI6MjA3MTIxNDA4MH0.8aXJwgeSQjDuffKt7nBw7nKzp4MvTh1o2SZr85cnwqM'

const supabase = createClient(supabaseUrl, supabaseAnonKey)

// Direct Supabase OAuth functions
export const signInWithGoogle = async () => {
  try {
    const { data, error } = await supabase.auth.signInWithOAuth({
      provider: 'google',
      options: {
        redirectTo: 'http://localhost:3000/auth/supabase/callback'
      }
    })
    
    if (error) throw error
    return data
  } catch (error) {
    console.error('Supabase Google OAuth error:', error)
    throw error
  }
}

export const handleSupabaseCallback = async () => {
  try {
    const { data, error } = await supabase.auth.getSession()
    
    if (error) throw error
    
    if (data.session) {
      // Store the Supabase session token
      localStorage.setItem('supabase_token', data.session.access_token)
      return data.session
    } else {
      throw new Error('No session found')
    }
  } catch (error) {
    console.error('Supabase callback error:', error)
    throw error
  }
}

export const signOut = async () => {
  try {
    const { error } = await supabase.auth.signOut()
    if (error) throw error
    
    // Clear stored tokens
    localStorage.removeItem('supabase_token')
  } catch (error) {
    console.error('Supabase sign out error:', error)
    throw error
  }
}

export const getCurrentUser = async () => {
  try {
    const { data: { user }, error } = await supabase.auth.getUser()
    
    if (error) throw error
    return user
  } catch (error) {
    console.error('Get current user error:', error)
    throw error
  }
}
