import React, { useState } from 'react';
import { useOrcaStore, Boat } from '../../store/useOrcaStore';
import { X, Check } from 'lucide-react';

const availableGrounds = [
  "Quilon Bank", "Wadge Bank", "Muthalapozhi Nearshore", 
  "Trivandrum Deep", "Kanyakumari Coast"
];

const BoatRegistrationModal: React.FC = () => {
  const { isBoatModalOpen, setBoatModalOpen, setActiveBoat } = useOrcaStore();
  
  const [formData, setFormData] = useState<Partial<Boat>>({
    hullClass: 'FRP Skiff',
    lengthM: 8.5,
    engineHp: 9.9,
    homeHarbour: 'Muthalapozhi',
    usualGrounds: []
  });

  if (!isBoatModalOpen) return null;

  const toggleGround = (ground: string) => {
    const current = formData.usualGrounds || [];
    if (current.includes(ground)) {
      setFormData({ ...formData, usualGrounds: current.filter(g => g !== ground) });
    } else {
      setFormData({ ...formData, usualGrounds: [...current, ground] });
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setActiveBoat({
      boatId: `B-${Math.random().toString(36).substr(2, 5).toUpperCase()}`,
      hullClass: formData.hullClass!,
      lengthM: Number(formData.lengthM),
      engineHp: Number(formData.engineHp),
      homeHarbour: formData.homeHarbour!,
      usualGrounds: formData.usualGrounds || []
    });
    setBoatModalOpen(false);
  };

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-2xl w-full max-w-md overflow-hidden">
        <div className="bg-slate-900 px-6 py-4 flex justify-between items-center">
          <h2 className="text-lg font-bold text-white">Register Boat Profile</h2>
          <button onClick={() => setBoatModalOpen(false)} className="text-gray-400 hover:text-white">
            <X className="w-5 h-5" />
          </button>
        </div>
        
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <div className="space-y-1">
            <label className="text-xs font-semibold text-gray-500 uppercase">Hull Class</label>
            <select 
              value={formData.hullClass}
              onChange={e => setFormData({...formData, hullClass: e.target.value})}
              className="w-full border rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 outline-none"
            >
              <option>FRP Skiff</option>
              <option>Plywood Canoe</option>
              <option>Mechanized Trawler</option>
            </select>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-1">
              <label className="text-xs font-semibold text-gray-500 uppercase">Length (m)</label>
              <input 
                type="number" step="0.1"
                value={formData.lengthM}
                onChange={e => setFormData({...formData, lengthM: parseFloat(e.target.value)})}
                className="w-full border rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 outline-none"
              />
            </div>
            <div className="space-y-1">
              <label className="text-xs font-semibold text-gray-500 uppercase">Engine (HP)</label>
              <input 
                type="number"
                value={formData.engineHp}
                onChange={e => setFormData({...formData, engineHp: parseInt(e.target.value)})}
                className="w-full border rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 outline-none"
              />
            </div>
          </div>

          <div className="space-y-1">
            <label className="text-xs font-semibold text-gray-500 uppercase">Home Harbour</label>
            <input 
              type="text"
              value={formData.homeHarbour}
              onChange={e => setFormData({...formData, homeHarbour: e.target.value})}
              className="w-full border rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 outline-none"
            />
          </div>

          <div className="space-y-2">
            <label className="text-xs font-semibold text-gray-500 uppercase">Usual Fishing Grounds (No Coordinates)</label>
            <div className="flex flex-wrap gap-2">
              {availableGrounds.map(ground => {
                const isSelected = formData.usualGrounds?.includes(ground);
                return (
                  <button
                    key={ground}
                    type="button"
                    onClick={() => toggleGround(ground)}
                    className={`px-3 py-1.5 rounded-full text-xs font-medium flex items-center border transition-colors ${
                      isSelected ? 'bg-blue-50 text-blue-700 border-blue-200' : 'bg-gray-50 text-gray-600 border-gray-200 hover:bg-gray-100'
                    }`}
                  >
                    {isSelected && <Check className="w-3 h-3 mr-1" />}
                    {ground}
                  </button>
                )
              })}
            </div>
          </div>

          <div className="pt-4 flex justify-end space-x-3 border-t mt-6">
            <button 
              type="button" 
              onClick={() => setBoatModalOpen(false)}
              className="px-4 py-2 text-sm font-medium text-gray-600 hover:text-gray-900 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors"
            >
              Cancel
            </button>
            <button 
              type="submit"
              className="px-4 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-lg shadow-sm transition-colors"
            >
              Save Profile
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default BoatRegistrationModal;
