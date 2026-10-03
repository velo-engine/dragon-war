module src

import velo.kine2d
import velo.serialize

// Every game component needs one registration line to be usable in .scene files and in the editor.
pub fn register_components(mut r serialize.Registry) {
	kine2d.register_builtins(mut r) // opt-in: the Kine2D skeleton component
	r.register[Game]()
	r.register[Hud]()
	r.register[Enemy]()
	r.register[Dragon]()
	r.register[Projectile]()
	r.register[FloatText]()
	r.register[MenuScreen]()
}
