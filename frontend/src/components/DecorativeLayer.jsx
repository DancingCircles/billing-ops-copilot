import cloud from "../assets/images/approach-clouds.png";
import helicopter from "../assets/images/purple-helicopter.png";

export function DecorativeLayer() {
  return (
    <div className="decor-layer" aria-hidden="true">
      <img className="heli-cutout" src={helicopter} alt="" />
      <img className="cloud-cutout cloud-left" src={cloud} alt="" />
      <img className="cloud-cutout cloud-right" src={cloud} alt="" />
    </div>
  );
}
