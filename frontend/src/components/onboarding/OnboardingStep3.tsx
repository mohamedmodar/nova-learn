
import React from 'react';
import { Label } from '@/components/ui/label';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { Slider } from '@/components/ui/slider';
import { OnboardingData } from '../../pages/Onboarding';

interface Props {
  data: OnboardingData;
  updateData: (data: Partial<OnboardingData>) => void;
}

const OnboardingStep3: React.FC<Props> = ({ data, updateData }) => {
  const learningFormats = [
    { value: 'short', label: 'Short videos (5-15 minutes)' },
    { value: 'long', label: 'Long-form content (30+ minutes)' },
    { value: 'text', label: 'Text-based tutorials' },
    { value: 'interactive', label: 'Interactive coding exercises' }
  ];

  return (
    <div className="space-y-6">
      <div className="space-y-3">
        <Label className="text-base font-medium">What's your preferred learning format?</Label>
        <RadioGroup
          value={data.learningFormat}
          onValueChange={(value) => updateData({ learningFormat: value })}
        >
          {learningFormats.map((format) => (
            <div key={format.value} className="flex items-center space-x-2">
              <RadioGroupItem value={format.value} id={format.value} />
              <Label htmlFor={format.value}>{format.label}</Label>
            </div>
          ))}
        </RadioGroup>
      </div>

      <div className="space-y-3">
        <Label className="text-base font-medium">
          How many hours per week can you dedicate to learning?
        </Label>
        <div className="px-4">
          <Slider
            value={[data.weeklyTime]}
            onValueChange={(value) => updateData({ weeklyTime: value[0] })}
            max={20}
            min={1}
            step={1}
            className="w-full"
          />
          <div className="flex justify-between text-sm text-gray-500 mt-1">
            <span>1 hour</span>
            <span>{data.weeklyTime} hours</span>
            <span>20+ hours</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default OnboardingStep3;
