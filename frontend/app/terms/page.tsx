import { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Terms of Service | PoseWeaver',
  description: 'Terms of Service for PoseWeaver - AI-powered writing assistant for roleplay and creative writing.',
}

export default function TermsPage() {
  return (
    <div className="min-h-screen bg-background">
      <div className="container max-w-4xl py-12">
        <div className="prose prose-slate dark:prose-invert max-w-none">
          <h1 className="text-4xl font-bold mb-8">Terms of Service</h1>
          <p className="text-muted-foreground mb-8"><strong>Effective Date: January 24, 2025</strong></p>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold mb-4">1. Acceptance of Terms</h2>
            <p>By accessing or using PoseWeaver ("Service"), you agree to be bound by these Terms of Service ("Terms"). If you disagree with any part of these terms, you may not access the Service.</p>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold mb-4">2. Description of Service</h2>
            <p>PoseWeaver is an AI-powered writing assistant platform designed for roleplay and creative writing, offering:</p>
            <ul className="list-disc pl-6 mt-2">
              <li>Character management and creation tools</li>
              <li>AI-powered pose enhancement and refinement</li>
              <li>Image description generation</li>
              <li>Writing analytics and style tools</li>
              <li>Subscription-based premium features</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold mb-4">3. User Accounts</h2>
            <h3 className="text-xl font-medium mb-2">3.1 Account Creation</h3>
            <ul className="list-disc pl-6 mb-4">
              <li>You must provide accurate and complete information when creating an account</li>
              <li>You are responsible for maintaining the security of your account credentials</li>
              <li>You must be at least 13 years old to use this Service</li>
            </ul>
            
            <h3 className="text-xl font-medium mb-2">3.2 Account Responsibilities</h3>
            <ul className="list-disc pl-6">
              <li>You are responsible for all activities that occur under your account</li>
              <li>You must notify us immediately of any unauthorized use of your account</li>
              <li>We reserve the right to suspend or terminate accounts that violate these Terms</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold mb-4">4. Subscription Plans and Billing</h2>
            <h3 className="text-xl font-medium mb-2">4.1 Subscription Tiers</h3>
            <ul className="list-disc pl-6 mb-4">
              <li><strong>Free Plan</strong>: Limited features with usage restrictions</li>
              <li><strong>Basic Plan</strong>: $9.99/month with enhanced features and higher usage limits</li>
              <li><strong>Pro Plan</strong>: $19.99/month with premium features and unlimited usage</li>
            </ul>
            
            <h3 className="text-xl font-medium mb-2">4.2 Billing Terms</h3>
            <ul className="list-disc pl-6 mb-4">
              <li>Subscriptions are billed monthly in advance</li>
              <li>All fees are non-refundable except as required by law</li>
              <li>We reserve the right to change pricing with 30 days notice</li>
              <li>Failed payments may result in service suspension</li>
            </ul>
            
            <h3 className="text-xl font-medium mb-2">4.3 Recharge Packs</h3>
            <ul className="list-disc pl-6">
              <li>Additional generation credits available for purchase</li>
              <li>Recharge packs do not expire but are tied to your account</li>
              <li>No refunds for unused recharge pack credits</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold mb-4">5. Acceptable Use Policy</h2>
            <h3 className="text-xl font-medium mb-2">5.1 Permitted Uses</h3>
            <ul className="list-disc pl-6 mb-4">
              <li>Creating original characters and roleplay content</li>
              <li>Enhancing writing for personal or collaborative storytelling</li>
              <li>Generating descriptions for creative projects</li>
              <li>Educational and artistic purposes</li>
            </ul>
            
            <h3 className="text-xl font-medium mb-2">5.2 Prohibited Uses</h3>
            <p className="mb-2">You may not use PoseWeaver to:</p>
            <ul className="list-disc pl-6">
              <li>Create, upload, or share illegal, harmful, or offensive content</li>
              <li>Violate intellectual property rights of others</li>
              <li>Harass, abuse, or harm other users</li>
              <li>Attempt to reverse engineer or exploit the Service</li>
              <li>Use the Service for commercial purposes without authorization</li>
              <li>Generate content that promotes violence, hate speech, or discrimination</li>
              <li>Create sexually explicit content involving minors</li>
              <li>Impersonate others or provide false information</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold mb-4">6. Content and Intellectual Property</h2>
            <h3 className="text-xl font-medium mb-2">6.1 User Content</h3>
            <ul className="list-disc pl-6 mb-4">
              <li>You retain ownership of content you create using PoseWeaver</li>
              <li>You grant us a limited license to process and store your content to provide the Service</li>
              <li>You are responsible for ensuring your content complies with these Terms</li>
            </ul>
            
            <h3 className="text-xl font-medium mb-2">6.2 AI-Generated Content</h3>
            <ul className="list-disc pl-6 mb-4">
              <li>AI-enhanced content is considered derivative of your original input</li>
              <li>You are responsible for reviewing and approving all AI-generated content</li>
              <li>We do not claim ownership of AI-generated content based on your prompts</li>
            </ul>
            
            <h3 className="text-xl font-medium mb-2">6.3 Platform Content</h3>
            <ul className="list-disc pl-6">
              <li>PoseWeaver's software, design, and documentation are protected by intellectual property laws</li>
              <li>You may not copy, modify, or distribute our proprietary content</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold mb-4">7. Privacy and Data Protection</h2>
            <ul className="list-disc pl-6">
              <li>Your privacy is important to us. Please review our Privacy Policy for details on data collection and use</li>
              <li>We implement security measures to protect your personal information</li>
              <li>You can request deletion of your account and associated data at any time</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold mb-4">8. AI Service Limitations</h2>
            <h3 className="text-xl font-medium mb-2">8.1 AI Accuracy</h3>
            <ul className="list-disc pl-6 mb-4">
              <li>AI-generated content may contain errors or inaccuracies</li>
              <li>We do not guarantee the quality or appropriateness of AI outputs</li>
              <li>Users should review and edit AI-generated content before use</li>
            </ul>
            
            <h3 className="text-xl font-medium mb-2">8.2 Service Availability</h3>
            <ul className="list-disc pl-6">
              <li>We strive for 99% uptime but cannot guarantee uninterrupted service</li>
              <li>Maintenance windows may temporarily affect service availability</li>
              <li>Third-party AI services may experience their own limitations</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold mb-4">9. Limitation of Liability</h2>
            <p className="mb-4">TO THE MAXIMUM EXTENT PERMITTED BY LAW:</p>
            <ul className="list-disc pl-6">
              <li>PoseWeaver is provided "as is" without warranties of any kind</li>
              <li>We are not liable for indirect, incidental, or consequential damages</li>
              <li>Our total liability is limited to the amount you paid for the Service in the past 12 months</li>
              <li>We are not responsible for user-generated content or third-party services</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold mb-4">10. Termination</h2>
            <h3 className="text-xl font-medium mb-2">10.1 Termination by You</h3>
            <ul className="list-disc pl-6 mb-4">
              <li>You may cancel your subscription at any time through your account settings</li>
              <li>Cancellation takes effect at the end of your current billing period</li>
              <li>You may delete your account and data through account settings</li>
            </ul>
            
            <h3 className="text-xl font-medium mb-2">10.2 Termination by Us</h3>
            <p className="mb-2">We may suspend or terminate your account if you:</p>
            <ul className="list-disc pl-6">
              <li>Violate these Terms of Service</li>
              <li>Engage in fraudulent or illegal activities</li>
              <li>Fail to pay subscription fees</li>
              <li>Abuse or misuse the Service</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold mb-4">11. Special Provisions for Roleplay Content</h2>
            <h3 className="text-xl font-medium mb-2">11.1 Creative Fiction</h3>
            <ul className="list-disc pl-6 mb-4">
              <li>PoseWeaver is designed for creative fiction and roleplay scenarios</li>
              <li>All character interactions are fictional and for entertainment purposes</li>
              <li>Users are responsible for distinguishing between fiction and reality</li>
            </ul>
            
            <h3 className="text-xl font-medium mb-2">11.2 Community Standards</h3>
            <ul className="list-disc pl-6">
              <li>Respect other users in shared spaces</li>
              <li>Follow established roleplay etiquette and community guidelines</li>
              <li>Report inappropriate behavior or content to our moderation team</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold mb-4">12. Contact Information</h2>
            <p>For questions about these Terms, please contact us at:</p>
            <ul className="list-disc pl-6 mt-2">
              <li>Email: legal@poseweaver.com</li>
              <li>Address: [Your Business Address]</li>
            </ul>
          </section>

          <div className="border-t pt-8 mt-12">
            <p className="text-sm text-muted-foreground">
              <strong>Last Updated: January 24, 2025</strong>
            </p>
            <p className="text-sm text-muted-foreground mt-2">
              By using PoseWeaver, you acknowledge that you have read, understood, and agree to be bound by these Terms of Service.
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
