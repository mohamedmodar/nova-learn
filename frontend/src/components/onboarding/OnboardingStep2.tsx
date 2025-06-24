
import React from 'react';
import { Label } from '@/components/ui/label';
import { Checkbox } from '@/components/ui/checkbox';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { OnboardingData } from '../../pages/Onboarding';

interface Props {
  data: OnboardingData;
  updateData: (data: Partial<OnboardingData>) => void;
}

const OnboardingStep2: React.FC<Props> = ({ data, updateData }) => {
  const technicalSkills = [
    'Python', 'Java', 'JavaScript', 'C++', 'SQL', 'HTML/CSS', 
    'React', 'Node.js', 'Machine Learning', 'Data Analysis', 'None'
  ];

  const priorCourses = [
    'Computer Science Fundamentals',
    'Web Development',
    'Data Science',
    'Machine Learning',
    'Mobile Development',
    'Database Management',
    'None'
  ];

  return (
    <div className="space-y-6">
      <div className="space-y-3">
        <Label className="text-base font-medium">What technical skills do you have? (Select all that apply)</Label>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
          {technicalSkills.map((skill) => (
            <div key={skill} className="flex items-center space-x-2">
              <Checkbox
                id={skill}
                checked={data.technicalSkills.includes(skill)}
                onCheckedChange={(checked) => {
                  if (checked) {
                    updateData({ technicalSkills: [...data.technicalSkills, skill] });
                  } else {
                    updateData({ 
                      technicalSkills: data.technicalSkills.filter(s => s !== skill) 
                    });
                  }
                }}
              />
              <Label htmlFor={skill} className="text-sm">{skill}</Label>
            </div>
          ))}
        </div>
      </div>

      <div className="space-y-3">
        <Label className="text-base font-medium">Do you understand programming basics?</Label>
        <RadioGroup
          value={data.programmingBasics ? 'yes' : 'no'}
          onValueChange={(value) => updateData({ programmingBasics: value === 'yes' })}
        >
          <div className="flex items-center space-x-2">
            <RadioGroupItem value="yes" id="prog-yes" />
            <Label htmlFor="prog-yes">Yes, I understand programming concepts</Label>
          </div>
          <div className="flex items-center space-x-2">
            <RadioGroupItem value="no" id="prog-no" />
            <Label htmlFor="prog-no">No, I'm new to programming</Label>
          </div>
        </RadioGroup>
      </div>

      <div className="space-y-3">
        <Label className="text-base font-medium">Have you taken any of these courses before?</Label>
        <div className="space-y-2">
          {priorCourses.map((course) => (
            <div key={course} className="flex items-center space-x-2">
              <Checkbox
                id={course}
                checked={data.priorCourses.includes(course)}
                onCheckedChange={(checked) => {
                  if (checked) {
                    updateData({ priorCourses: [...data.priorCourses, course] });
                  } else {
                    updateData({ 
                      priorCourses: data.priorCourses.filter(c => c !== course) 
                    });
                  }
                }}
              />
              <Label htmlFor={course} className="text-sm">{course}</Label>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default OnboardingStep2;
