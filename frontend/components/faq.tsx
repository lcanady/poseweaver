import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion"

const faqs = [
  {
    question: "Will this replace my creativity?",
    answer:
      "Absolutely not. Think of it as a creative partner. It handles the descriptive heavy lifting, freeing you up to focus on dialogue, action, and plot. You always have the final say and can edit the enhanced post as you see fit.",
  },
  {
    question: "What platforms does PoseWeaver support?",
    answer:
      "Our parser is designed to be flexible. It can intelligently identify posts and ignore system messages from most platforms, including Discord, forums, and Google Docs. If you encounter a format it struggles with, let us know and we'll work on adding support.",
  },
  {
    question: "Is my character data secure?",
    answer:
      "Yes. Your character profiles are private to your account and are only used to inform the AI for your post enhancements. We do not share your data or use it to train models for other users.",
  },
  {
    question: "Can I customize the AI's writing style?",
    answer:
      "Yes. Beyond the 'Minimal', 'Balanced', and 'Elaborate' settings, the Premium plan allows for fine-tuning. You can provide examples of your own writing to guide the AI toward a style that perfectly matches your own.",
  },
]

export function Faq() {
  return (
    <section id="faq" className="container py-12 lg:py-24">
      <div className="text-center space-y-4 mb-12">
        <h2 className="text-3xl md:text-4xl font-bold">Frequently Asked Questions</h2>
      </div>
      <div className="max-w-3xl mx-auto">
        <Accordion type="single" collapsible>
          {faqs.map((faq, index) => (
            <AccordionItem key={index} value={`item-${index}`}>
              <AccordionTrigger className="text-lg">{faq.question}</AccordionTrigger>
              <AccordionContent className="text-base text-muted-foreground">{faq.answer}</AccordionContent>
            </AccordionItem>
          ))}
        </Accordion>
      </div>
    </section>
  )
}
