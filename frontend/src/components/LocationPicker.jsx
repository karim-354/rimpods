import React, { useEffect, useState } from "react";
import { MapContainer, TileLayer, Marker, useMapEvents, useMap } from "react-leaflet";
import L from "leaflet";
import "leaflet/dist/leaflet.css";

// Fix default Leaflet marker icons (bundler can't resolve the default image paths)
const markerIcon = new L.Icon({
  iconUrl: "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon.png",
  iconRetinaUrl: "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon-2x.png",
  shadowUrl: "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png",
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41],
});

const DEFAULT_CENTER = [-6.2088, 106.8456]; // Jakarta fallback

// Places/updates the pin when the user clicks anywhere on the map
function ClickHandler({ onPick }) {
  useMapEvents({
    click(e) {
      onPick(e.latlng.lat, e.latlng.lng);
    },
  });
  return null;
}

// Recenters the map ONLY when `target` changes (use-my-location / returning customer),
// not while the user is dragging the pin.
function Recenter({ target }) {
  const map = useMap();
  useEffect(() => {
    if (target && target[0] && target[1]) {
      map.setView([target[0], target[1]], 16);
    }
  }, [target, map]);
  return null;
}

export default function LocationPicker({ lat, lng, onChange }) {
  const hasPos = Boolean(lat && lng);
  const numLat = hasPos ? parseFloat(lat) : null;
  const numLng = hasPos ? parseFloat(lng) : null;

  // recenter target: set on initial load (returning customer) and "use my location"
  const [recenterTo, setRecenterTo] = useState(hasPos ? [numLat, numLng] : null);

  // If coordinates arrive later (e.g. autofill from phone lookup), recenter once
  useEffect(() => {
    if (hasPos) setRecenterTo([parseFloat(lat), parseFloat(lng)]);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [lat, lng]);

  const handlePick = (la, ln) => {
    onChange(String(la), String(ln));
  };

  const useMyLocation = () => {
    if (!navigator.geolocation) return;
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setRecenterTo([pos.coords.latitude, pos.coords.longitude]);
        handlePick(pos.coords.latitude, pos.coords.longitude);
      },
      () => {}
    );
  };

  return (
    <div className="space-y-2">
      <div className="flex items-start justify-between gap-2">
        <p className="text-xs text-slate-400">
          Klik / geser pin tepat di rumah tujuan untuk membuka kurir instan (Gojek, Grab, Lalamove, Paxel).
        </p>
        <button
          type="button"
          onClick={useMyLocation}
          className="text-xs text-blue-400 underline whitespace-nowrap shrink-0"
        >
          Lompat ke lokasi saya
        </button>
      </div>

      <div className="rounded-xl overflow-hidden border border-slate-700" style={{ height: 240 }}>
        <MapContainer
          center={hasPos ? [numLat, numLng] : DEFAULT_CENTER}
          zoom={hasPos ? 16 : 11}
          style={{ height: "100%", width: "100%" }}
          scrollWheelZoom={false}
        >
          <TileLayer
            attribution='&copy; OpenStreetMap contributors'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />
          <ClickHandler onPick={handlePick} />
          <Recenter target={recenterTo} />
          {hasPos && (
            <Marker
              position={[numLat, numLng]}
              icon={markerIcon}
              draggable={true}
              eventHandlers={{
                dragend: (e) => {
                  const m = e.target.getLatLng();
                  handlePick(m.lat, m.lng);
                },
              }}
            />
          )}
        </MapContainer>
      </div>

      {hasPos ? (
        <p className="text-xs text-emerald-400">
          Lokasi terkunci ({numLat.toFixed(5)}, {numLng.toFixed(5)}) — kurir instan aktif.
        </p>
      ) : (
        <p className="text-xs text-amber-400">
          Belum pin lokasi — hanya ekspedisi reguler yang tampil. Klik peta untuk pin rumah Anda.
        </p>
      )}
    </div>
  );
}
