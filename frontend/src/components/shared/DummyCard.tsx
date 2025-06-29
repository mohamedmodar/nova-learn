import React from 'react';

export const DummyCard = ({ title }: { title: string }) => {
  return (
    <div className="p-4 border rounded-lg bg-green-100 text-green-800">
      <p className="font-bold">This is a Dummy Card</p>
      <p>It is rendering the title: {title}</p>
    </div>
  );
}; 