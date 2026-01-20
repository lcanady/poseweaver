import { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Privacy Policy | PoseWeaver',
  description: 'Privacy Policy for PoseWeaver - Learn how we protect your data and privacy.',
}

export default function PrivacyPage() {
  return (
    <div className="min-h-screen bg-background">
      <div className="container max-w-4xl py-12">
        <div className="prose prose-slate dark:prose-invert max-w-none">
          <h1 className="text-4xl font-bold mb-8">Privacy Policy</h1>
          <p className="text-muted-foreground mb-8"><strong>Effective Date: January 24, 2025</strong></p>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold mb-4">1. Introduction</h2>
            <p>PoseWeaver ("we," "our," or "us") is committed to protecting your privacy. This Privacy Policy explains how we collect, use, disclose, and safeguard your information when you use our AI-powered writing assistant platform.</p>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold mb-4">2. Information We Collect</h2>
            
            <h3 className="text-xl font-medium mb-2">2.1 Personal Information</h3>
            <p className="mb-2">We collect information you provide directly to us:</p>
            <ul className="list-disc pl-6 mb-4">
              <li><strong>Account Information</strong>: Email address, display name, password (encrypted)</li>
              <li><strong>Profile Information</strong>: Bio, preferences, settings, avatar images</li>
              <li><strong>Billing Information</strong>: Payment details processed securely through Stripe</li>
              <li><strong>Communication Data</strong>: Messages sent to our support team</li>
            </ul>

            <h3 className="text-xl font-medium mb-2">2.2 Content Data</h3>
            <ul className="list-disc pl-6 mb-4">
              <li><strong>Characters</strong>: Character profiles, descriptions, and associated metadata</li>
              <li><strong>Writing Content</strong>: Original poses, enhanced text, and refinement requests</li>
              <li><strong>Images</strong>: Uploaded images for description generation</li>
              <li><strong>Usage Data</strong>: Generation counts, feature usage, and interaction patterns</li>
            </ul>

            <h3 className="text-xl font-medium mb-2">2.3 Technical Information</h3>
            <ul className="list-disc pl-6 mb-4">
              <li><strong>Device Information</strong>: Browser type, operating system, device identifiers</li>
              <li><strong>Usage Analytics</strong>: Pages visited, features used, session duration</li>
              <li><strong>Log Data</strong>: IP addresses, access times, error logs, performance metrics</li>
              <li><strong>Cookies</strong>: Authentication tokens, preferences, and analytics data</li>
            </ul>

            <h3 className="text-xl font-medium mb-2">2.4 AI Interaction Data</h3>
            <ul className="list-disc pl-6">
              <li><strong>Prompts and Inputs</strong>: Text and images submitted to AI services</li>
              <li><strong>AI Outputs</strong>: Generated content and enhancement results</li>
              <li><strong>Feedback Data</strong>: User ratings and refinement requests</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold mb-4">3. How We Use Your Information</h2>
            
            <h3 className="text-xl font-medium mb-2">3.1 Service Provision</h3>
            <ul className="list-disc pl-6 mb-4">
              <li>Authenticate users and maintain account security</li>
              <li>Process AI enhancement and description generation requests</li>
              <li>Store and manage user-created characters and content</li>
              <li>Provide customer support and respond to inquiries</li>
              <li>Process payments and manage subscriptions</li>
            </ul>

            <h3 className="text-xl font-medium mb-2">3.2 Service Improvement</h3>
            <ul className="list-disc pl-6 mb-4">
              <li>Analyze usage patterns to improve features and performance</li>
              <li>Develop new AI capabilities and writing tools</li>
              <li>Optimize user experience and interface design</li>
              <li>Conduct research and development for platform enhancement</li>
            </ul>

            <h3 className="text-xl font-medium mb-2">3.3 Communication</h3>
            <ul className="list-disc pl-6">
              <li>Send service-related notifications and updates</li>
              <li>Provide customer support and technical assistance</li>
              <li>Share important changes to terms or policies</li>
              <li>Send marketing communications (with consent)</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold mb-4">4. Information Sharing and Disclosure</h2>
            
            <h3 className="text-xl font-medium mb-2">4.1 Third-Party Service Providers</h3>
            <p className="mb-2">We share information with trusted partners who assist in operating our platform:</p>
            
            <div className="mb-4">
              <p className="font-medium">AI Services (OpenRouter AI)</p>
              <ul className="list-disc pl-6 mt-1">
                <li>Text and image inputs for processing</li>
                <li>Generated content for quality assurance</li>
                <li>Usage metrics for service optimization</li>
              </ul>
            </div>

            <div className="mb-4">
              <p className="font-medium">Payment Processing (Stripe)</p>
              <ul className="list-disc pl-6 mt-1">
                <li>Billing information for subscription and purchase processing</li>
                <li>Transaction data for payment verification</li>
                <li>Fraud prevention and security monitoring</li>
              </ul>
            </div>

            <h3 className="text-xl font-medium mb-2">4.2 Legal Requirements</h3>
            <p className="mb-2">We may disclose information when required by law:</p>
            <ul className="list-disc pl-6">
              <li>Court orders, subpoenas, or legal processes</li>
              <li>Government investigations or regulatory compliance</li>
              <li>Protection of rights, property, or safety</li>
              <li>Prevention of fraud or illegal activities</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold mb-4">5. Data Security</h2>
            
            <h3 className="text-xl font-medium mb-2">5.1 Security Measures</h3>
            <ul className="list-disc pl-6 mb-4">
              <li><strong>Encryption</strong>: Data encrypted in transit and at rest</li>
              <li><strong>Access Controls</strong>: Role-based access with authentication requirements</li>
              <li><strong>Monitoring</strong>: Continuous security monitoring and threat detection</li>
              <li><strong>Regular Audits</strong>: Security assessments and vulnerability testing</li>
            </ul>

            <h3 className="text-xl font-medium mb-2">5.2 Data Storage</h3>
            <ul className="list-disc pl-6">
              <li><strong>Location</strong>: Data stored in secure cloud infrastructure</li>
              <li><strong>Backup</strong>: Regular backups with encryption and access controls</li>
              <li><strong>Retention</strong>: Data retained only as long as necessary for service provision</li>
              <li><strong>Deletion</strong>: Secure deletion processes for account termination</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold mb-4">6. Your Privacy Rights</h2>
            
            <h3 className="text-xl font-medium mb-2">6.1 Access and Control</h3>
            <ul className="list-disc pl-6 mb-4">
              <li><strong>Account Access</strong>: View and update your account information</li>
              <li><strong>Data Export</strong>: Request copies of your personal data</li>
              <li><strong>Content Management</strong>: Edit, delete, or download your created content</li>
              <li><strong>Settings Control</strong>: Manage privacy preferences and notifications</li>
            </ul>

            <h3 className="text-xl font-medium mb-2">6.2 Data Rights (GDPR/CCPA)</h3>
            <p className="mb-2">If you are in the EU, UK, or California, you have additional rights:</p>
            <ul className="list-disc pl-6">
              <li><strong>Right to Access</strong>: Request information about data processing</li>
              <li><strong>Right to Rectification</strong>: Correct inaccurate personal data</li>
              <li><strong>Right to Erasure</strong>: Request deletion of personal data</li>
              <li><strong>Right to Portability</strong>: Receive data in a machine-readable format</li>
              <li><strong>Right to Object</strong>: Opt-out of certain data processing activities</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold mb-4">7. Cookies and Tracking</h2>
            
            <h3 className="text-xl font-medium mb-2">7.1 Cookie Types</h3>
            <ul className="list-disc pl-6 mb-4">
              <li><strong>Essential Cookies</strong>: Required for authentication and core functionality</li>
              <li><strong>Analytics Cookies</strong>: Track usage patterns and performance metrics</li>
              <li><strong>Preference Cookies</strong>: Remember user settings and preferences</li>
              <li><strong>Security Cookies</strong>: Detect suspicious activity and prevent abuse</li>
            </ul>

            <h3 className="text-xl font-medium mb-2">7.2 Cookie Management</h3>
            <ul className="list-disc pl-6">
              <li>Browser settings allow you to control cookie acceptance</li>
              <li>Disabling essential cookies may limit platform functionality</li>
              <li>Third-party cookies governed by respective privacy policies</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold mb-4">8. Children's Privacy</h2>
            
            <h3 className="text-xl font-medium mb-2">8.1 Age Requirements</h3>
            <ul className="list-disc pl-6 mb-4">
              <li>PoseWeaver is intended for users 13 years and older</li>
              <li>Users under 18 should have parental consent</li>
              <li>We do not knowingly collect data from children under 13</li>
            </ul>

            <h3 className="text-xl font-medium mb-2">8.2 Parental Controls</h3>
            <ul className="list-disc pl-6">
              <li>Parents can request information about their child's account</li>
              <li>Account deletion available upon parental request</li>
              <li>Enhanced privacy protections for users under 18</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold mb-4">9. AI and Machine Learning</h2>
            
            <h3 className="text-xl font-medium mb-2">9.1 AI Processing</h3>
            <ul className="list-disc pl-6 mb-4">
              <li>Your content is processed by AI services to provide enhancements</li>
              <li>AI models may learn from aggregated, anonymized usage patterns</li>
              <li>Individual content is not used to train AI models without consent</li>
            </ul>

            <h3 className="text-xl font-medium mb-2">9.2 Content Generation</h3>
            <ul className="list-disc pl-6">
              <li>AI-generated content is based on your inputs and preferences</li>
              <li>We do not claim ownership of AI-generated content</li>
              <li>You are responsible for reviewing and approving AI outputs</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold mb-4">10. Data Retention</h2>
            
            <h3 className="text-xl font-medium mb-2">10.1 Retention Periods</h3>
            <ul className="list-disc pl-6 mb-4">
              <li><strong>Account Data</strong>: Retained while account is active plus 30 days</li>
              <li><strong>Content Data</strong>: Retained until user deletion or account termination</li>
              <li><strong>Usage Analytics</strong>: Aggregated data retained for up to 2 years</li>
              <li><strong>Legal Requirements</strong>: Data retained as required by applicable law</li>
            </ul>

            <h3 className="text-xl font-medium mb-2">10.2 Deletion Process</h3>
            <ul className="list-disc pl-6">
              <li>Account deletion removes personal data within 30 days</li>
              <li>Some data may be retained in anonymized form for analytics</li>
              <li>Backup systems may retain data for additional 90 days</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold mb-4">11. Contact Information</h2>
            
            <h3 className="text-xl font-medium mb-2">11.1 Privacy Inquiries</h3>
            <p className="mb-2">For questions about this Privacy Policy or your data rights:</p>
            <ul className="list-disc pl-6 mb-4">
              <li><strong>Email</strong>: privacy@poseweaver.com</li>
              <li><strong>Response Time</strong>: Within 30 days</li>
            </ul>

            <h3 className="text-xl font-medium mb-2">11.2 Data Protection Officer</h3>
            <p className="mb-2">For GDPR-related inquiries:</p>
            <ul className="list-disc pl-6">
              <li><strong>Email</strong>: dpo@poseweaver.com</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold mb-4">12. Platform-Specific Privacy Considerations</h2>
            
            <h3 className="text-xl font-medium mb-2">12.1 Character Data</h3>
            <ul className="list-disc pl-6 mb-4">
              <li>Character profiles are private by default</li>
              <li>Featured character showcase requires explicit opt-in</li>
              <li>Character data is not shared with other users without permission</li>
            </ul>

            <h3 className="text-xl font-medium mb-2">12.2 Writing Content</h3>
            <ul className="list-disc pl-6 mb-4">
              <li>Original poses and enhanced content remain private</li>
              <li>AI processing occurs in secure, isolated environments</li>
              <li>Content is not used for training without explicit consent</li>
            </ul>

            <h3 className="text-xl font-medium mb-2">12.3 Image Processing</h3>
            <ul className="list-disc pl-6">
              <li>Uploaded images processed only for description generation</li>
              <li>Images are not stored permanently after processing</li>
              <li>No facial recognition or biometric data collection</li>
            </ul>
          </section>

          <div className="border-t pt-8 mt-12">
            <p className="text-sm text-muted-foreground">
              <strong>Last Updated: January 24, 2025</strong>
            </p>
            <p className="text-sm text-muted-foreground mt-2">
              This Privacy Policy is designed to be transparent about our data practices while protecting your privacy rights. If you have questions or concerns, please don't hesitate to contact us.
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
