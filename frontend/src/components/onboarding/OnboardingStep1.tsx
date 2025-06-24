
import React from 'react';
import { Label } from '@/components/ui/label';
import { Slider } from '@/components/ui/slider';
import { Checkbox } from '@/components/ui/checkbox';
import { OnboardingData } from '../../pages/Onboarding';

interface Props {
  data: OnboardingData;
  updateData: (data: Partial<OnboardingData>) => void;
}

const OnboardingStep1: React.FC<Props> = ({ data, updateData }) => {
  const courseTypes = ['Internal University Courses', 'External Online Courses', 'Both'];

  return (
    <div className="space-y-6">
      <div className="space-y-3">
        <Label className="text-base font-medium">How confident are you with learning new topics?</Label>
        <div className="px-4">
          <Slider
            value={[data.learningConfidence]}
            onValueChange={(value) => updateData({ learningConfidence: value[0] })}
            max={5}
            min={1}
            step={1}
            className="w-full"
          />
          <div className="flex justify-between text-sm text-gray-500 mt-1">
            <span>Not confident</span>
            <span>Very confident</span>
          </div>
        </div>
      </div>

      <div className="space-y-3">
        <Label className="text-base font-medium">What type of courses are you interested in?</Label>
        <div className="space-y-2">
          {courseTypes.map((type) => (
            <div key={type} className="flex items-center space-x-2">
              <Checkbox
                id={type}
                checked={data.coursePreference.includes(type)}
                onCheckedChange={(checked) => {
                  if (checked) {
                    updateData({ coursePreference: [...data.coursePreference, type] });
                  } else {
                    updateData({ 
                      coursePreference: data.coursePreference.filter(t => t !== type) 
                    });
                  }
                }}
              />
              <Label htmlFor={type} className="text-sm">{type}</Label>
            </div>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="space-y-3">
          <Label className="text-base font-medium">English Proficiency</Label>
          <div className="px-4">
            <Slider
              value={[data.englishProficiency]}
              onValueChange={(value) => updateData({ englishProficiency: value[0] })}
              max={3}
              min={1}
              step={1}
              className="w-full"
            />
            <div className="flex justify-between text-sm text-gray-500 mt-1">
              <span>Basic</span>
              <span>Advanced</span>
            </div>
          </div>
        </div>

        <div className="space-y-3">
          <Label className="text-base font-medium">Math Proficiency</Label>
          <div className="px-4">
            <Slider
              value={[data.mathProficiency]}
              onValueChange={(value) => updateData({ mathProficiency: value[0] })}
              max={3}
              min={1}
              step={1}
              className="w-full"
            />
            <div className="flex justify-between text-sm text-gray-500 mt-1">
              <span>Basic</span>
              <span>Advanced</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default OnboardingStep1;
