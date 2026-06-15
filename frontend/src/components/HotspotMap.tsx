import { MapContainer, Marker, Popup, TileLayer } from "react-leaflet";
import L from "leaflet";
import type { MapLocation } from "../types";
import "leaflet/dist/leaflet.css";

const defaultIcon = L.icon({
  iconUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
  iconRetinaUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png",
  shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41],
});
L.Marker.prototype.options.icon = defaultIcon;

interface HotspotMapProps {
  locations: MapLocation[];
  onSelect?: (location: MapLocation) => void;
}

export default function HotspotMap({ locations, onSelect }: HotspotMapProps) {
  if (locations.length === 0) {
    return (
      <div className="flex h-80 items-center justify-center rounded-3xl border border-forest-100 bg-forest-50 text-forest-700/70">
        표시할 관찰지가 없습니다.
      </div>
    );
  }

  const center = {
    lat: locations.reduce((sum, l) => sum + l.latitude, 0) / locations.length,
    lng: locations.reduce((sum, l) => sum + l.longitude, 0) / locations.length,
  };

  return (
    <div className="overflow-hidden rounded-3xl border border-forest-100 shadow-sm">
      <MapContainer center={center} zoom={7} scrollWheelZoom className="h-96 w-full">
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        {locations.map((spot) => (
          <Marker key={spot.id} position={[spot.latitude, spot.longitude]}>
            <Popup>
              <div className="text-sm">
                <p className="font-semibold">{spot.name}</p>
                <p>{spot.species_name}</p>
                <p>점수 {(spot.observation_score * 100).toFixed(0)}</p>
                {onSelect && (
                  <button
                    className="mt-2 rounded bg-forest-700 px-2 py-1 text-white"
                    onClick={() => onSelect(spot)}
                  >
                    상세 보기
                  </button>
                )}
              </div>
            </Popup>
          </Marker>
        ))}
      </MapContainer>
    </div>
  );
}
