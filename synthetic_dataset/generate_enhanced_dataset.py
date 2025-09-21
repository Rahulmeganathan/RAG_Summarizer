import json
import random
import datetime
from typing import List, Dict, Tuple, Any
from collections import Counter
import os

class EnhancedMeetingDatasetGenerator:
    def __init__(self, character_profiles_path: str):
        """Initialize the dataset generator with character profiles."""
        with open(character_profiles_path, 'r') as f:
            self.characters = json.load(f)
        
        # Initialize generation parameters
        self.start_date = datetime.date(2024, 1, 1)
        self.end_date = datetime.date(2024, 6, 30)
        self.meetings_count = 0
        self.generated_meetings = []
        
        # Meeting distribution rules
        self.business_meeting_ratio = 0.65
        self.family_meeting_ratio = 0.20
        self.mixed_meeting_ratio = 0.15
        
        # Time patterns
        self.business_hours = [(9, 17)]  # 9 AM to 5 PM
        self.family_hours = [(18, 21), (7, 9)]  # Evening and early morning
        
    def generate_meeting_id(self, date: datetime.date) -> str:
        """Generate unique meeting ID."""
        self.meetings_count += 1
        return f"MTG_{date.strftime('%Y_%m_%d')}_{self.meetings_count:03d}"
    
    def select_participants_by_rules(self, meeting_type: str) -> List[Dict[str, str]]:
        """Select participants based on meeting type rules."""
        participants = [{"name": "Arjun Vasanth", "role": "founder"}]
        
        if meeting_type == "business":
            # Business meeting logic
            meeting_subtype = random.choice([
                "investor", "team", "mentor", "peer_networking"
            ])
            
            if meeting_subtype == "investor":
                # 1-2 investors + optional mentor
                investor_names = list(self.characters["investors"].keys())
                selected_investors = random.sample(investor_names, 
                                                 random.randint(1, min(2, len(investor_names))))
                for inv in selected_investors:
                    participants.append({"name": inv, "role": "investor"})
                    
                # Optional mentor
                if random.random() < 0.3:
                    mentor_names = list(self.characters["mentors"].keys())
                    mentor = random.choice(mentor_names)
                    participants.append({"name": mentor, "role": "mentor"})
                    
            elif meeting_subtype == "team":
                # 2-3 team members
                team_names = [name for name, data in self.characters["peers_team"].items() 
                             if data["role"] == "team"]
                selected_team = random.sample(team_names, 
                                            random.randint(1, min(3, len(team_names))))
                for member in selected_team:
                    participants.append({"name": member, "role": "team"})
                    
            elif meeting_subtype == "mentor":
                # 1 mentor + optional peer
                mentor_names = list(self.characters["mentors"].keys())
                mentor = random.choice(mentor_names)
                participants.append({"name": mentor, "role": "mentor"})
                
                if random.random() < 0.4:
                    peer_names = [name for name, data in self.characters["peers_team"].items()
                                 if data["role"] == "peer"]
                    if peer_names:
                        peer = random.choice(peer_names)
                        participants.append({"name": peer, "role": "peer"})
                        
            elif meeting_subtype == "peer_networking":
                # 2-4 peers
                peer_names = [name for name, data in self.characters["peers_team"].items()
                             if data["role"] == "peer"]
                selected_peers = random.sample(peer_names,
                                             random.randint(1, min(4, len(peer_names))))
                for peer in selected_peers:
                    participants.append({"name": peer, "role": "peer"})
                    
        elif meeting_type == "family":
            # Family meeting logic
            family_names = list(self.characters["family"].keys())
            selected_family = random.sample(family_names,
                                          random.randint(1, len(family_names)))
            for member in selected_family:
                participants.append({"name": member, "role": "family"})
                
        elif meeting_type == "mixed":
            # Mixed meeting: family concerns about business
            # Always include spouse, sometimes parents
            participants.append({"name": "Meera Vasanth", "role": "family"})
            
            if random.random() < 0.5:
                parents = ["Dr. Krishnan Vasanth", "Lakshmi Vasanth"]
                selected_parent = random.choice(parents)
                participants.append({"name": selected_parent, "role": "family"})
                
            # Sometimes include mentor for guidance
            if random.random() < 0.3:
                mentor_names = list(self.characters["mentors"].keys())
                mentor = random.choice(mentor_names)
                participants.append({"name": mentor, "role": "mentor"})
        
        return participants
    
    def select_topics(self, meeting_type: str) -> List[str]:
        """Select 2 topics based on meeting type and logical combinations."""
        topics = self.characters["topics"]
        
        # Define topic combinations based on meeting type
        if meeting_type == "business":
            business_topics = [
                "AI Insurance POC Development",
                "Investor Pitch & Feedback Sessions", 
                "Product Demo & Technical Reviews",
                "Market Strategy & Competition Analysis",
                "Team Building & Hiring",
                "Regulatory Compliance Discussions",
                "Customer Acquisition & Sales Pipeline",
                "Technology Infrastructure & Scaling"
            ]
            # Define complementary pairs
            complementary_pairs = [
                ("AI Insurance POC Development", "Investor Pitch & Feedback Sessions"),
                ("Product Demo & Technical Reviews", "Market Strategy & Competition Analysis"),
                ("Team Building & Hiring", "Technology Infrastructure & Scaling"),
                ("Customer Acquisition & Sales Pipeline", "Market Strategy & Competition Analysis"),
                ("AI Insurance POC Development", "Product Demo & Technical Reviews"),
                ("Investor Pitch & Feedback Sessions", "Market Strategy & Competition Analysis")
            ]
            
            if random.random() < 0.7:  # 70% chance for complementary topics
                return list(random.choice(complementary_pairs))
            else:
                return random.sample(business_topics, 2)
                
        elif meeting_type == "family":
            family_topics = [
                "Family Financial Concerns",
                "Stress Management & Work-Life Balance"
            ]
            other_topics = [
                "AI Insurance POC Development",
                "Investor Pitch & Feedback Sessions"
            ]
            # Mix family concerns with business context
            return [random.choice(family_topics), random.choice(other_topics)]
            
        elif meeting_type == "mixed":
            # Mixed meetings focus on intersection of personal and business
            return [
                "Family Financial Concerns",
                "Stress Management & Work-Life Balance"
            ]
            
        return random.sample(topics, 2)
    
    def generate_meeting_time(self, meeting_type: str, date: datetime.date) -> str:
        """Generate realistic meeting time based on type and day."""
        if meeting_type == "business":
            # Business hours: 9 AM - 5 PM
            hour = random.randint(9, 17)
            minute = random.choice([0, 15, 30, 45])  # Standard meeting times
        elif meeting_type == "family":
            # Family time: evenings or early morning weekends
            if date.weekday() >= 5:  # Weekend
                hour = random.randint(9, 20)
            else:  # Weekday
                hour = random.randint(19, 21)
            minute = random.choice([0, 30])
        else:  # mixed
            # Mixed meetings often happen in evenings
            hour = random.randint(18, 20)
            minute = random.choice([0, 30])
            
        return f"{hour:02d}:{minute:02d}"
    
    def generate_location(self, meeting_type: str, participants: List[Dict]) -> str:
        """Generate realistic location based on meeting type and participants."""
        if meeting_type == "business":
            if any(p["role"] == "investor" for p in participants):
                investor_names = [p["name"] for p in participants if p["role"] == "investor"]
                if "Priya Sharma" in investor_names:
                    return "Nexus Venture Partners Office, Bangalore"
                elif "Rajesh Gupta" in investor_names:
                    return "The Leela Palace Hotel, Bangalore"
                elif "David Chen" in investor_names:
                    return "Video Call (Singapore)"
                else:
                    return "Investor Office, Bangalore"
            elif any(p["role"] == "team" for p in participants):
                return "InsureAI Office, Koramangala, Bangalore"
            else:
                return random.choice([
                    "Café Coffee Day, HSR Layout", 
                    "The Toit Brewpub, Indiranagar",
                    "Video Call"
                ])
        elif meeting_type == "family":
            return "Home, Whitefield, Bangalore"
        else:  # mixed
            return random.choice([
                "Home, Whitefield, Bangalore",
                "Café Coffee Day near home"
            ])
    
    def generate_elaborate_dialogue(self, participants: List[Dict], topics: List[str], 
                                   meeting_type: str) -> List[Dict[str, Any]]:
        """Generate realistic, elaborate dialogue with startup jargon and emotional authenticity."""
        minutes = []
        jargon = self.characters["jargon_categories"]
        
        # Opening - Arjun usually starts with elaborate context setting
        timestamp_minutes = 0
        
        # Generate elaborate opening based on meeting type
        if meeting_type == "business" and any(p["role"] == "investor" for p in participants):
            opening_texts = [
                f"Thank you both for making time in your busy schedules to meet with us today. I'm really excited to share the progress we've made on our AI insurance platform over the past quarter. Our machine learning model has achieved {random.randint(92, 96)}% accuracy in automated claims processing, which is significantly higher than the industry standard of around 85%. We're processing real insurance claims data from three pilot customers, and the feedback has been overwhelmingly positive. The key breakthrough came when we solved the challenge of handling unstructured documents - medical reports, police reports, and damage assessments - which traditionally required manual review. Our NLP pipeline can now extract relevant information with remarkable precision, reducing processing time from weeks to just 2-3 days. I believe we're at an inflection point where we can demonstrate clear ROI to insurance companies and start scaling our operations.",
                
                f"I really appreciate you both taking this meeting, especially given how competitive the fundraising environment has become. Let me walk you through where we stand with our AI insurance POC and why I believe we're uniquely positioned to capture this market opportunity. Over the past three months, we've been working intensively with our pilot customers to refine our machine learning algorithms. The results have exceeded our expectations - we're now achieving {random.randint(90, 95)}% accuracy in automated claims assessment, which translates to massive cost savings for insurance companies. What's particularly exciting is that our solution addresses the $40 billion problem of claims fraud detection. Our AI can identify suspicious patterns and anomalies that human adjusters often miss, potentially saving insurers millions per year. We've also made significant progress on regulatory compliance, working closely with IRDAI to ensure our platform meets all necessary requirements for the Indian insurance market.",
                
                f"Thanks for agreeing to this follow-up meeting. I know our last conversation raised some important questions about scalability and market penetration, so I wanted to address those concerns directly and share some exciting developments. Since we last spoke, we've successfully onboarded two additional insurance partners - one specializing in motor insurance and another in health insurance. This has allowed us to test our AI across different insurance verticals and validate our hypothesis about horizontal scalability. The technical architecture we've built is genuinely revolutionary - we're using a combination of computer vision for document analysis, natural language processing for unstructured text, and advanced machine learning for pattern recognition. Our API can integrate with any existing insurance management system in under 48 hours, which is a huge competitive advantage. The market opportunity is enormous - the Indian insurance industry processes over 50 million claims annually, and our solution can automate at least 70% of that volume."
            ]
        elif meeting_type == "family":
            opening_texts = [
                "I know I've been completely consumed by work lately, and I can see the concern in your eyes every time I come home after midnight or skip family dinners. I wanted to sit down with all of you and be completely transparent about what's happening with the company and why these next few months are so critical for our future. The truth is, we're at a make-or-break moment. The funding landscape has become incredibly challenging - investors are much more cautious than they were a year ago, and they're demanding stronger metrics and clearer paths to profitability. But at the same time, our technology is finally ready for prime time. We're solving a real problem that insurance companies desperately need solved, and we have the technical capabilities to deliver a solution that could transform the entire industry.",
                
                "I understand that my work schedule has been putting a strain on our family, and I don't want you to think that I'm prioritizing the business over our relationships. But I need you to understand the magnitude of the opportunity we're facing and why I believe this period of intense focus will ultimately benefit all of us. We're building something that could genuinely change the insurance industry in India. Every major insurance company struggles with claims processing - it's slow, expensive, and prone to errors. Our AI solution can automate 70% of that work while actually improving accuracy. If we can prove this at scale and secure the right funding, we're looking at a potential exit valuation of $100-200 million within the next three years. That would set up our family financially for life.",
                
                "I wanted to bring everyone together today because I know there's been tension about my work hours and the stress I've been under. You deserve to understand exactly what we're working toward and why I believe it's worth the sacrifice we're all making. The AI insurance market in India is expected to reach $2.8 billion by 2027, and we have a genuine first-mover advantage. Our technology can reduce claims processing costs by 60% while improving customer satisfaction scores. We've already proven this with our pilot customers, and now it's about scaling and securing the capital we need to expand rapidly before competitors catch up."
            ]
        else:  # mixed meetings
            opening_texts = [
                "I've been thinking a lot about our conversation last week, and I realize I haven't been doing a good job of balancing my commitment to the business with my responsibilities to our family. The pressure from investors and the demands of building this company have been consuming me, but I don't want that to come at the expense of our relationship or my health. At the same time, I truly believe we're on the verge of something extraordinary with this AI insurance platform, and I'm struggling with how to manage both priorities effectively.",
                
                "I know the past few months have been difficult for all of us, and I appreciate your patience as I've been navigating the challenges of fundraising and product development. I wanted to talk openly about where we stand as a family and as a business, because these two aspects of my life are becoming increasingly intertwined. The success of the company will ultimately determine our financial security and long-term opportunities, but I don't want to sacrifice our happiness and well-being in the pursuit of that success."
            ]
        
        minutes.append({
            "timestamp": f"00:{timestamp_minutes:02d}:00",
            "speaker": "Arjun Vasanth",
            "text": random.choice(opening_texts)
        })
        timestamp_minutes += random.randint(3, 5)
        
        # Generate elaborate responses from other participants
        for i, participant in enumerate(participants[1:]):  # Skip Arjun
            char_data = self.get_character_data(participant["name"])
            if char_data:
                response_text = self.generate_elaborate_character_response(
                    participant, char_data, topics, meeting_type, jargon, i
                )
                minutes.append({
                    "timestamp": f"00:{timestamp_minutes:02d}:00",
                    "speaker": participant["name"],
                    "text": response_text
                })
                timestamp_minutes += random.randint(2, 4)
        
        # Add multiple rounds of detailed back-and-forth conversation
        for round_num in range(random.randint(3, 6)):
            # Arjun's detailed follow-up
            followup_text = self.generate_elaborate_arjun_followup(topics, meeting_type, jargon, round_num)
            minutes.append({
                "timestamp": f"00:{timestamp_minutes:02d}:00", 
                "speaker": "Arjun Vasanth",
                "text": followup_text
            })
            timestamp_minutes += random.randint(2, 4)
            
            # Other participants respond with detailed commentary
            if len(participants) > 1:
                participant = random.choice(participants[1:])
                char_data = self.get_character_data(participant["name"])
                if char_data:
                    response_text = self.generate_elaborate_character_response(
                        participant, char_data, topics, meeting_type, jargon, round_num + 10
                    )
                    minutes.append({
                        "timestamp": f"00:{timestamp_minutes:02d}:00",
                        "speaker": participant["name"], 
                        "text": response_text
                    })
                    timestamp_minutes += random.randint(2, 4)
        
        return minutes
    
    def get_character_data(self, name: str) -> Dict:
        """Get character data from profiles."""
        for category in ["investors", "family", "mentors", "peers_team"]:
            if name in self.characters[category]:
                return self.characters[category][name]
        return {}
    
    def generate_elaborate_character_response(self, participant: Dict, char_data: Dict, 
                                            topics: List[str], meeting_type: str, 
                                            jargon: Dict, response_round: int) -> str:
        """Generate elaborate, character-specific responses."""
        role = participant["role"]
        name = participant["name"]
        
        if role == "investor":
            if name == "Priya Sharma":
                investor_responses = [
                    f"Arjun, I appreciate the technical progress you've outlined, and the {random.randint(92, 96)}% accuracy rate is impressive. However, as we move toward a potential investment decision, I need to understand the business fundamentals much more clearly. What's your current customer acquisition cost, and how does that compare to the lifetime value of your customers? I'm particularly concerned about your go-to-market strategy and whether you can scale your sales efforts efficiently. The insurance industry is notoriously relationship-driven and slow to adopt new technologies. How are you planning to overcome these barriers? Additionally, I'd like to see a detailed analysis of your total addressable market and how you're planning to capture market share from established players who have decades of relationships with insurance companies.",
                    
                    f"The technology sounds promising, but I'm seeing a lot of competition in the insurtech space, and frankly, many promising startups have struggled to achieve meaningful scale. What I need to understand is your sustainable competitive advantage. How do you prevent larger technology companies or established insurance software providers from replicating your solution? Your burn rate concerns me as well - at your current spending levels, how long is your runway, and what specific milestones do you need to hit to justify our investment? I also need clarity on your regulatory strategy. Insurance is heavily regulated, and any AI solution needs to comply with IRDAI guidelines. Have you received any regulatory approvals, and what's your timeline for full compliance?",
                    
                    f"Let me be direct about my concerns, Arjun. While your technical achievements are noteworthy, I'm not seeing the kind of traction that typically precedes a successful Series A round. Your pilot customers are encouraging, but do you have signed contracts with committed revenue? What's your monthly recurring revenue, and what's the growth trajectory? Insurance companies move slowly, and pilot projects don't always translate to full deployments. I need to see evidence that you can convert these pilots into substantial, long-term contracts. Also, your team composition worries me. Do you have insurance industry veterans who understand the nuances of this market? Technical expertise alone won't be sufficient to navigate the complex sales cycles and regulatory requirements you'll face."
                ]
            elif name == "Rajesh Gupta":
                investor_responses = [
                    f"Arjun, I've been through this journey myself with multiple startups, and I can see you're facing the classic challenges that every B2B SaaS company encounters when trying to scale. The technology you've built is solid, but the real question is execution. I've seen brilliant technical teams struggle because they underestimated the complexity of enterprise sales, especially in a conservative industry like insurance. Your pilot results are encouraging, but how long did it take to close those deals? What was the decision-making process like? Insurance companies typically have 6-12 month sales cycles, and they'll want extensive proof of concept, security audits, and integration testing. Do you have the resources and patience to manage these lengthy sales processes while maintaining your burn rate?",
                    
                    f"I'm impressed by your technical progress, but let me share some hard-earned wisdom from my experience at Flipkart and other ventures. Market timing is everything, and while AI is hot right now, insurance companies are inherently risk-averse. They won't adopt your solution just because it's innovative - they need compelling ROI and bulletproof reliability. Have you quantified the exact cost savings your solution provides? Can you guarantee 99.9% uptime? What happens if your AI makes a mistake that costs an insurance company millions in wrongful claims? These are the questions that will come up in every enterprise sales conversation. Also, consider your pricing strategy carefully. Insurance companies are used to paying for software as a percentage of premiums processed, not as a flat SaaS fee.",
                    
                    f"The competitive landscape is something you need to think about strategically. Yes, you have first-mover advantage in India, but international players like Shift Technology and Tractable are already expanding globally. How do you defend against well-funded competitors who might enter the Indian market? Your technology might be superior today, but that advantage can erode quickly. What I'd like to see is a broader platform strategy - can you expand beyond claims processing into underwriting, fraud detection, or customer service? The companies that succeed in enterprise software are those that become deeply embedded in their customers' workflows. Single-point solutions are vulnerable to disruption."
                ]
            else:  # David Chen
                investor_responses = [
                    f"Arjun, from a global perspective, I'm seeing similar AI-driven insurance solutions across multiple markets, and the question is whether your approach can scale beyond India. The technology you've developed appears sophisticated, but I need to understand your international expansion strategy. How adaptable is your platform to different regulatory environments? Insurance regulations vary significantly across countries, and what works in India might not work in Southeast Asia or other emerging markets. Additionally, I'm curious about your data strategy. Insurance is fundamentally about risk assessment, and the quality of your AI depends entirely on the data you train it on. Do you have access to sufficient historical claims data to ensure your models are robust? How do you handle data privacy and cross-border data transfer requirements?",
                    
                    f"The unit economics you've presented need more scrutiny, particularly if you're planning to expand internationally. Customer acquisition costs tend to increase significantly when you're entering new markets where you don't have established relationships or brand recognition. How do you plan to adapt your go-to-market strategy for different cultural and business environments? I'm also concerned about your technology infrastructure. Can your platform handle the scale and complexity of processing claims in multiple languages and currencies? What about integration with different core insurance systems that vary by country? These technical challenges often prove more costly and time-consuming than founders anticipate.",
                    
                    f"Let me share a perspective from our portfolio companies that have attempted similar international expansions. The insurance industry is deeply local - relationships, regulations, and business practices vary dramatically across markets. Simply translating your software isn't sufficient. You need local partnerships, regulatory expertise, and often significant customization for each market. This requires substantial capital and can dilute your focus from perfecting your solution in your home market. Have you considered a partnership strategy with established insurance software vendors who already have international presence? This might be a more capital-efficient way to scale globally while maintaining focus on your core technology development."
                ]
            
            return random.choice(investor_responses)
            
        elif role == "family":
            if name == "Meera Vasanth":
                family_responses = [
                    f"Arjun, I appreciate you taking the time to explain what's happening with the business, but I need you to understand the impact this is having on our family. You've been working 16-hour days for the past six months, and it's affecting not just your health, but our relationship and our plans for the future. I know you believe in this opportunity, and I want to support you, but I'm worried about what we're sacrificing in the process. We had planned to start looking for a house this year, and we've put that on hold because of the uncertainty with the business. Our savings are dwindling because you're not taking a full salary, and I'm carrying the entire financial burden of our household expenses on my TCS income. When was the last time we had a proper conversation that wasn't about work or investors or funding? I feel like I'm losing my husband to this company.",
                    
                    f"I understand that you're passionate about this technology and the potential impact it could have, but I need to know that you have a realistic backup plan. What if the funding doesn't come through? What if the customers don't materialize the way you expect? You've invested two years of our lives and most of our savings into this venture, and while I admire your dedication, I'm scared about what happens if it doesn't work out. We're not 22 years old anymore - we need to think about our long-term financial security, starting a family, buying a home. I've been supportive of your entrepreneurial dreams, but I need to see some concrete milestones and timelines. How much longer are we going to live in this state of uncertainty? What specific goals need to be achieved for you to consider this venture successful?",
                    
                    f"The stress you're under is visible, Arjun, and it's affecting every aspect of our lives. You barely sleep, you're constantly on your phone during dinner, and when you do talk about work, it's always about problems - investors who are difficult, customers who are slow to decide, team members who aren't performing. I know building a company is challenging, but I need to see that you're taking care of yourself and our relationship in the process. Can we establish some boundaries? Maybe no work calls after 9 PM, or at least one weekend day that's completely dedicated to us? I'm not asking you to abandon your dreams, but I need to feel like I'm still a priority in your life. Our marriage has to be stronger than your business, and right now, I'm not sure you see it that way."
                ]
            elif name == "Dr. Krishnan Vasanth":
                family_responses = [
                    f"Son, I've been watching you for the past year, and while I admire your technical skills and your ambition, I'm concerned about the path you've chosen. In my 35 years in banking, I learned that financial security comes from steady, predictable income and careful risk management. What you're doing is essentially gambling with your future and our family's stability. Yes, there's potential for significant returns, but there's also a very real possibility of losing everything. Have you considered what happens if this venture fails? You're 29 years old - these are crucial years for building your career and financial foundation. If you spend another two years on this startup and it doesn't succeed, you'll be 31 with a gap in your traditional work experience. How easy will it be to find a good job then?",
                    
                    f"I understand that the technology sector offers opportunities that didn't exist in my generation, but I also understand business fundamentals that haven't changed. You need customers who are willing to pay, you need predictable revenue, and you need to manage your expenses carefully. From what you've told us, you have pilot customers but no guaranteed revenue, you're burning through savings, and you're dependent on investors who may or may not provide funding. This sounds incredibly risky to me. In banking, we had a saying: 'Don't put all your eggs in one basket.' Right now, you've put everything - your time, money, career, and family's well-being - into this single venture. What's your contingency plan?",
                    
                    f"I'm also worried about the toll this is taking on your health and your marriage. Meera is a wonderful girl, and she's been incredibly supportive of your ambitions, but I can see the strain in her eyes. You're asking a lot of her - to support the household financially while you pursue this uncertain venture, to accept a lifestyle of constant stress and uncertainty, to put her own dreams and plans on hold. That's not fair to her, and it's not sustainable for your marriage. Success in business means nothing if you lose your family in the process. I think you need to set some clear deadlines and exit criteria. If certain milestones aren't met by specific dates, you should consider returning to a more traditional career path."
                ]
            else:  # Lakshmi Vasanth
                family_responses = [
                    f"Beta, every time I see you, you look more tired and stressed. You've lost weight, you have dark circles under your eyes, and you seem to carry the weight of the world on your shoulders. I know you want to achieve great things, and I'm proud of your intelligence and dedication, but I'm worried about what this pressure is doing to your body and mind. When was the last time you had a proper meal or a full night's sleep? You used to love cooking with me and watching movies on Sunday afternoons. Now, even when you're physically present, your mind is always somewhere else, thinking about work problems. I've raised you to be ambitious, but not at the cost of your health and happiness.",
                    
                    f"I see how hard Meera is trying to support you, and my heart goes out to her. She's managing all the household responsibilities while also working full-time to support both of you financially. That's a lot of pressure for a young woman. I watch her making excuses for your absence at family gatherings, explaining to relatives why you can't attend weddings or festivals. She's sacrificing her own social life and happiness to support your dreams. I hope you appreciate what a treasure she is and that you're not taking her support for granted. Marriage is a partnership, beta, and partnerships require balance and mutual consideration.",
                    
                    f"I've lived through many economic ups and downs, and I've seen how quickly circumstances can change. While I admire your confidence in this business venture, I think it's important to have realistic expectations and backup plans. Life has a way of surprising us, and the most successful people are those who can adapt to changing circumstances. I'm not asking you to give up on your dreams, but I want you to be smart about managing risk. Can you pursue this opportunity while also maintaining some financial security? Perhaps you could consult or work part-time while building your business? There's wisdom in taking calculated risks rather than betting everything on a single outcome."
                ]
            
            return random.choice(family_responses)
            
        elif role == "mentor":
            if name == "Vikram Malhotra":
                mentor_responses = [
                    f"Arjun, having been through multiple startup cycles at Paytm and other ventures, I can see you're hitting the classic inflection point that determines whether a startup scales successfully or struggles indefinitely. The technology you've built is impressive, but the real challenge now is building a repeatable, scalable sales process. In B2B SaaS, especially in enterprise sales, product-market fit isn't just about having a working product - it's about having a product that customers will buy predictably and repeatedly. I've seen brilliant technical teams fail because they couldn't crack the sales puzzle. You need to focus intensively on understanding your customer's buying process. Who are the decision makers? What's their budget cycle? What ROI metrics do they use to justify technology investments? Map out your entire sales funnel and identify where prospects are dropping off.",
                    
                    f"One thing I learned the hard way is that early customers often have very different needs than mainstream customers. Your pilot customers might be innovators who are willing to work with incomplete solutions, but scaling requires appealing to the early majority who are much more risk-averse. They want proven solutions, strong references, and minimal integration complexity. Are you ready for that transition? Also, think carefully about your pricing strategy. I've seen startups price too low initially to win customers, then struggle to raise prices later. Insurance companies have significant budgets for technology solutions - don't undervalue what you're providing. If you can demonstrate clear ROI, they'll pay premium prices for a solution that works reliably.",
                    
                    f"From a fundraising perspective, investors at this stage want to see momentum, not just potential. They want evidence that you can acquire customers systematically and retain them successfully. What's your monthly recurring revenue growth rate? What's your customer retention rate? How much are customers expanding their usage over time? These metrics matter more than your technology's accuracy or your total addressable market size. Focus on creating a compelling growth story with clear milestones and predictable patterns. Also, consider whether you're ready for the operational complexity that comes with scaling. Do you have the infrastructure, processes, and team to support 10x more customers? Scaling too fast without proper foundations can kill a promising company."
                ]
            else:  # Anita Krishnan
                mentor_responses = [
                    f"Arjun, as someone who has navigated similar challenges in the healthtech space, I want you to know that what you're experiencing - the investor skepticism, the long sales cycles, the pressure on personal relationships - is completely normal for B2B startups targeting regulated industries. The key is maintaining perspective and not letting short-term setbacks derail your long-term vision. That said, I think you need to be more strategic about managing your energy and resources. Building a startup is a marathon, not a sprint, and burning out doesn't serve anyone. I've learned that the most successful entrepreneurs are those who can maintain their effectiveness over years, not months. That requires setting boundaries, delegating effectively, and taking care of your physical and mental health.",
                    
                    f"Regarding fundraising, remember that rejection is part of the process. In our healthtech startup, we heard 'no' from 47 investors before finding the right partners. Each rejection taught us something valuable about our pitch, our market positioning, or our business model. Don't take it personally, and don't let it shake your confidence in the fundamentals of what you're building. However, do listen carefully to the patterns in investor feedback. If multiple investors are raising similar concerns, those concerns probably reflect real issues that need to be addressed. Are they questioning your market size? Your competitive positioning? Your team's ability to execute? Use this feedback to strengthen your business, not just your pitch.",
                    
                    f"I also want to address the personal toll this is taking on you and your family. I've been where you are - working impossible hours, constantly stressed about funding, feeling like the weight of everyone's expectations is on your shoulders. It's not sustainable, and it's not necessary. The best business decisions come from a place of clarity and calm, not panic and exhaustion. Have you considered bringing in an advisor or mentor who can provide objective perspective when you're too close to the problem? Sometimes an outside voice can see solutions that aren't visible from the inside. Also, remember that your relationship with Meera is one of your greatest assets. Don't sacrifice your most important partnership for your business partnership."
                ]
            
            return random.choice(mentor_responses)
            
        elif role == "team":
            team_responses = [
                f"Arjun, I've been working on the ML pipeline optimization for the past month, and I'm seeing some encouraging improvements in our model performance. We've managed to reduce false positive rates by 12% while maintaining our overall accuracy above 94%. The new ensemble approach we implemented is working particularly well for complex fraud detection scenarios. However, I'm concerned about our data quality issues. We're still seeing inconsistencies in how different insurance companies format their claims data, and this is affecting our model's reliability. I think we need to invest more time in building robust data preprocessing pipelines. Also, our current infrastructure might not scale well beyond 10,000 claims per day. We should start planning for a more distributed architecture if we expect to handle enterprise-level volumes.",
                
                f"From a technical perspective, our API integration process has improved significantly. We can now onboard new insurance partners in under 48 hours, which is a major competitive advantage. However, I'm seeing some concerning patterns in our customer feedback. Several pilot customers have mentioned that our user interface isn't intuitive for their claims adjusters. Remember, these are people who have been doing manual claims processing for decades - they need a very simple, guided experience. I think we should invest in UX research and redesign some of our core workflows. Also, we need to address the latency issues that come up during peak processing periods. Some customers are experiencing delays when they submit large batches of claims simultaneously."
            ]
            return random.choice(team_responses)
            
        elif role == "peer":
            peer_responses = [
                f"Man, I completely understand what you're going through. We're facing almost identical challenges at our startup - the same investor skepticism, the same long enterprise sales cycles, the same pressure to show traction quickly. I think the insurance industry is just inherently conservative, and that works against all of us who are trying to bring innovation to the space. But I've also learned some things that might be helpful. First, don't underestimate the power of customer references. Once you have one successful implementation, use that customer as your champion with others. Insurance executives trust their peers more than they trust startup founders. Second, consider partnering with established players rather than trying to replace them entirely. We've had success positioning ourselves as a technology partner to existing insurance software vendors rather than a direct competitor.",
                
                f"The fundraising environment is brutal right now for all of us. Investors are demanding much higher traction levels than they were two years ago. But I've noticed that the startups that are succeeding are those with the strongest unit economics and clearest paths to profitability. Have you modeled out exactly when you'll break even? Can you show investors a realistic timeline to positive cash flow? I think the days of growth-at-all-costs are over - investors want to see sustainable business models. Also, don't neglect the importance of building relationships with potential acquirers. Sometimes an acquisition can be a better outcome than trying to build an independent unicorn, especially in a market as challenging as insurance."
            ]
            return random.choice(peer_responses)
        
        return "I understand the challenges we're facing and appreciate the opportunity to discuss them."
    
    def generate_elaborate_arjun_followup(self, topics: List[str], meeting_type: str, jargon: Dict, round_num: int) -> str:
        """Generate Arjun's elaborate follow-up responses with stress and technical details."""
        
        if meeting_type == "business":
            business_responses = [
                f"I appreciate those concerns, and let me address them directly with some specific data points. Our customer acquisition cost has actually been trending downward as we've refined our sales process - we're now at about $12,000 per enterprise customer, which compares favorably to the industry standard of $15-20K for B2B SaaS solutions in this space. The lifetime value calculation is admittedly complex in insurance because contracts tend to be multi-year with variable usage, but our pilot customers are processing an average of 1,200 claims per month through our platform, which translates to roughly $8,000 in monthly recurring revenue per customer. If we can maintain that usage level, we're looking at LTV of around $180,000 per customer over a three-year period. The challenge, as you've rightly identified, is scaling our sales efforts while maintaining these unit economics.",
                
                f"You're absolutely right about the competitive landscape, and I've been thinking about this extensively. Our sustainable competitive advantage comes from three key areas: first, our deep integration with Indian regulatory requirements - we've spent 18 months working directly with IRDAI officials to ensure our AI models comply with local insurance regulations. Second, our data advantage - we've processed over 2.5 million historical claims from our pilot partners, which gives us training data that competitors simply don't have access to. Third, our technical architecture is genuinely differentiated - we're using a novel approach that combines transformer-based NLP models with computer vision for document analysis, wrapped in an ensemble framework that continuously learns from human feedback. It would take a competitor at least 12-18 months to replicate this technical stack, assuming they could access similar training data.",
                
                f"Let me walk you through our regulatory strategy in detail, because I think this is actually one of our strongest moats. We've been working closely with IRDAI for the past year, and we have preliminary approval for our AI models under their current guidelines for automated claims processing. More importantly, we've been participating in their working group on AI governance in insurance, which means we have early insight into upcoming regulatory changes. Our compliance framework includes full audit trails for every AI decision, explainability features that allow human adjusters to understand why our algorithm reached specific conclusions, and fail-safes that escalate complex cases to human review. We're not just compliant with current regulations - we're helping to shape future regulatory frameworks for AI in insurance."
            ]
            return random.choice(business_responses)
            
        elif meeting_type == "family":
            family_responses = [
                f"I hear everything you're saying, and I know I haven't been the husband or family member you deserve over these past months. The truth is, I've been so consumed by the daily crises - investor calls, customer issues, technical problems - that I've lost sight of what really matters. But I need you to understand that we're genuinely close to a breakthrough. Two of our pilot customers are ready to sign annual contracts worth $150,000 each, and we have three more in advanced negotiations. If we can close these deals over the next 60 days, it changes everything - our recurring revenue will be sufficient to support both the business and our family's needs. I'm not asking for unlimited patience, but I am asking for 90 more days to prove that this can work. If we don't hit these milestones by the end of next quarter, I promise I'll seriously consider returning to a traditional career path.",
                
                f"You're right that I haven't been taking care of myself, and that's affecting all of us. I've been operating in constant crisis mode, reacting to whatever urgent issue comes up each day rather than taking a strategic approach to building the business and maintaining our relationship. Starting this week, I want to establish some non-negotiable boundaries: no work calls after 9 PM, no laptop use during family dinners, and at least one full day each weekend that's completely dedicated to us. I also think we should start seeing a counselor together - not because our marriage is in crisis, but because I want to make sure we're communicating effectively during this stressful period. Building a company shouldn't come at the expense of building our life together.",
                
                f"I know the financial uncertainty is scary, and I take full responsibility for putting us in this position. Let me share exactly where we stand: we have enough savings to cover our personal expenses for four more months if I continue taking no salary from the company. The business has enough funding to operate for six months at current burn rates. If we close the contracts I mentioned, I can start taking a $8,000 monthly salary starting in January, which covers most of our household expenses. If we secure the Series A funding we're pursuing, I can normalize my salary and we can get back on track with our original plans - buying a house, starting a family, building the life we've always talked about. I understand that these are all 'ifs,' but they're realistic possibilities based on concrete opportunities we're actively pursuing."
            ]
            return random.choice(family_responses)
            
        else:  # mixed meetings
            mixed_responses = [
                f"I've been struggling with this balance between pursuing an opportunity that could transform our lives and maintaining the stability and happiness that you deserve right now. The business reality is that we're at a critical juncture - the next three months will largely determine whether this venture succeeds or fails. But the personal reality is that I can't achieve business success at the expense of losing the most important relationships in my life. I think the solution has to involve better boundaries and more realistic expectations. Instead of working seven days a week, I need to protect our time together and trust that focused, strategic work will be more effective than exhausted, round-the-clock grinding.",
                
                f"What I've learned over these past months is that sustainable success requires sustainable practices. I can't build a company that lasts if I burn out in the process, and I can't build wealth that matters if I lose my family while pursuing it. I want to propose a modified approach: I'll commit to specific work hours and family hours, I'll be more transparent about business milestones and timelines, and I'll actively involve you in major decisions that affect our future. This company should enhance our life together, not replace it. If I can't figure out how to build the business while maintaining our relationship, then I'm not as smart as I think I am."
            ]
            return random.choice(mixed_responses)
    
    def generate_action_items(self, participants: List[Dict], topics: List[str], 
                            meeting_type: str, meeting_date: datetime.date) -> List[Dict]:
        """Generate logical action items based on meeting discussion."""
        action_items = []
        
        # Calculate due dates
        due_date_options = [
            meeting_date + datetime.timedelta(days=7),   # 1 week
            meeting_date + datetime.timedelta(days=14),  # 2 weeks
            meeting_date + datetime.timedelta(days=21),  # 3 weeks
        ]
        
        if meeting_type == "business":
            if any(p["role"] == "investor" for p in participants):
                # Investor meeting action items
                action_items.extend([
                    {
                        "assigned_to": "Arjun Vasanth",
                        "task": f"Prepare comprehensive business metrics report including detailed CAC, LTV, and churn analysis with month-over-month trends for the past 6 months",
                        "due_date": random.choice(due_date_options).isoformat(),
                        "priority": "high"
                    },
                    {
                        "assigned_to": "Arjun Vasanth", 
                        "task": f"Create detailed competitive analysis document outlining our differentiation strategy and sustainable competitive advantages in the AI insurance market",
                        "due_date": random.choice(due_date_options).isoformat(),
                        "priority": "high"
                    }
                ])
            elif any(p["role"] == "team" for p in participants):
                # Team meeting action items
                action_items.extend([
                    {
                        "assigned_to": "Arjun Vasanth",
                        "task": f"Review and approve the ML pipeline optimization roadmap and allocate resources for infrastructure scaling to handle 50K+ claims per day",
                        "due_date": random.choice(due_date_options).isoformat(),
                        "priority": "medium"
                    },
                    {
                        "assigned_to": random.choice([p["name"] for p in participants if p["role"] == "team"]),
                        "task": "Conduct user experience research with pilot customers and propose UI/UX improvements for the claims processing dashboard",
                        "due_date": random.choice(due_date_options).isoformat(), 
                        "priority": "high"
                    }
                ])
        elif meeting_type == "family":
            # Family meeting action items
            action_items.extend([
                {
                    "assigned_to": "Arjun Vasanth",
                    "task": "Establish and implement clear work-life boundaries including no work calls after 9 PM and dedicated family time on weekends",
                    "due_date": (meeting_date + datetime.timedelta(days=3)).isoformat(),
                    "priority": "high"
                },
                {
                    "assigned_to": "Arjun Vasanth",
                    "task": "Schedule weekly family meetings to provide transparent updates on business progress and address any concerns",
                    "due_date": (meeting_date + datetime.timedelta(days=7)).isoformat(),
                    "priority": "medium"
                }
            ])
        elif meeting_type == "mixed":
            # Mixed meeting action items  
            action_items.extend([
                {
                    "assigned_to": "Arjun Vasanth",
                    "task": "Develop a comprehensive plan balancing business milestones with family commitments and share timeline with family members",
                    "due_date": (meeting_date + datetime.timedelta(days=7)).isoformat(),
                    "priority": "high"
                },
                {
                    "assigned_to": "Arjun Vasanth",
                    "task": "Research and schedule couples counseling sessions to improve communication during this stressful business phase",
                    "due_date": (meeting_date + datetime.timedelta(days=14)).isoformat(), 
                    "priority": "medium"
                }
            ])
        
        return action_items[:random.randint(1, 3)]  # 1-3 action items per meeting
    
    def generate_meetings(self, total_meetings: int = 55) -> List[Dict]:
        """Generate the complete dataset of meetings."""
        meetings = []
        
        # Calculate meeting distribution
        business_count = int(total_meetings * self.business_meeting_ratio)
        family_count = int(total_meetings * self.family_meeting_ratio) 
        mixed_count = total_meetings - business_count - family_count
        
        meeting_types = (["business"] * business_count + 
                        ["family"] * family_count + 
                        ["mixed"] * mixed_count)
        random.shuffle(meeting_types)
        
        # Generate dates across the period
        total_days = (self.end_date - self.start_date).days
        dates = []
        
        for i in range(total_meetings):
            # More frequent meetings during intense periods (March-May)
            if random.random() < 0.7:  # 70% of meetings in peak period
                # Peak period: March-May 2024
                peak_start = datetime.date(2024, 3, 1)
                peak_end = datetime.date(2024, 5, 31)
                peak_days = (peak_end - peak_start).days
                day_offset = random.randint(0, peak_days)
                meeting_date = peak_start + datetime.timedelta(days=day_offset)
            else:
                # Distributed across full period
                day_offset = random.randint(0, total_days)
                meeting_date = self.start_date + datetime.timedelta(days=day_offset)
            
            dates.append(meeting_date)
        
        dates.sort()  # Chronological order
        
        # Generate meetings
        for i, (meeting_type, meeting_date) in enumerate(zip(meeting_types, dates)):
            participants = self.select_participants_by_rules(meeting_type)
            topics = self.select_topics(meeting_type) 
            meeting_time = self.generate_meeting_time(meeting_type, meeting_date)
            location = self.generate_location(meeting_type, participants)
            minutes = self.generate_elaborate_dialogue(participants, topics, meeting_type)
            action_items = self.generate_action_items(participants, topics, meeting_type, meeting_date)
            
            meeting = {
                "meeting_id": self.generate_meeting_id(meeting_date),
                "meeting_date": meeting_date.isoformat(),
                "meeting_time": meeting_time,
                "location": location,
                "participants": participants,
                "topics": topics,
                "meeting_type": meeting_type,
                "minutes": minutes,
                "action_items": action_items
            }
            
            meetings.append(meeting)
            
        self.generated_meetings = meetings
        return meetings
    
    def save_meetings(self, output_dir: str):
        """Save individual meeting files and summary."""
        os.makedirs(output_dir, exist_ok=True)
        
        # Create enhanced_meetings directory
        enhanced_dir = os.path.join(output_dir, "enhanced_meetings")
        os.makedirs(enhanced_dir, exist_ok=True)
        
        # Save individual meeting files
        for i, meeting in enumerate(self.generated_meetings, 1):
            filename = f"enhanced_meeting_{i:03d}.json"
            filepath = os.path.join(enhanced_dir, filename)
            with open(filepath, 'w') as f:
                json.dump(meeting, f, indent=2)
        
        print(f"Generated {len(self.generated_meetings)} enhanced meetings")
        print(f"Saved to: {enhanced_dir}")

def main():
    """Main function to generate the enhanced dataset."""
    # File paths
    base_dir = r"C:\Users\Ranesh RK\Downloads\projects\RetrievalPOC\synthetic_dataset"
    character_profiles_path = os.path.join(base_dir, "character_profiles.json")
    
    # Initialize generator
    generator = EnhancedMeetingDatasetGenerator(character_profiles_path)
    
    # Generate meetings
    print("Generating enhanced synthetic meeting dataset with elaborate dialogues...")
    meetings = generator.generate_meetings(total_meetings=55)
    
    # Save results
    generator.save_meetings(base_dir)
    
    print("\nEnhanced dataset generation completed successfully!")
    print(f"Total meetings generated: {len(meetings)}")
    print("Each meeting now contains much longer, more realistic dialogue!")

if __name__ == "__main__":
    main()