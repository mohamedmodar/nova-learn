
import React from 'react';
import { Label } from '@/components/ui/label';
import { Checkbox } from '@/components/ui/checkbox';
import { OnboardingData } from '../../pages/Onboarding';

interface Props {
  data: OnboardingData;
  updateData: (data: Partial<OnboardingData>) => void;
}

const OnboardingStep4: React.FC<Props> = ({ data, updateData }) => {
  const learningGoals = [
    'Career advancement',
    'Personal interest',
    'Academic requirements',
    'Professional certification',
    'Skill development',
    'Job preparation'
  ];

  const learningInterests = [
    'Data Science',
    'Web Development',
    'Machine Learning',
    'Mobile Development',
    'Cloud Computing',
    'Cybersecurity',
    'UI/UX Design',
    'DevOps',
    'Artificial Intelligence',
    'Blockchain'
  ];

  return (
    <div className="space-y-6">
      <div className="space-y-3">
        <Label className="text-base font-medium">What are your learning goals?</Label>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
          {learningGoals.map((goal) => (
            <div key={goal} className="flex items-center space-x-2">
              <Checkbox
                id={goal}
                checked={data.learningGoals.includes(goal)}
                onCheckedChange={(checked) => {
                  if (checked) {
                    updateData({ learningGoals: [...data.learningGoals, goal] });
                  } else {
                    updateData({ 
                      learningGoals: data.learningGoals.filter(g => g !== goal) 
                    });
                  }
                }}
              />
              <Label htmlFor={goal} className="text-sm">{goal}</Label>
            </div>
          ))}
        </div>
      </div>

      <div className="space-y-3">
        <Label className="text-base font-medium">What topics are you most interested in?</Label>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
          {learningInterests.map((interest) => (
            <div key={interest} className="flex items-center space-x-2">
              <Checkbox
                id={interest}
                checked={data.learningInterests.includes(interest)}
                onCheckedChange={(checked) => {
                  if (checked) {
                    updateData({ learningInterests: [...data.learningInterests, interest] });
                  } else {
                    updateData({ 
                      learningInterests: data.learningInterests.filter(i => i !== interest) 
                    });
                  }
                }}
              />
              <Label htmlFor={interest} className="text-sm">{interest}</Label>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default OnboardingStep4;
