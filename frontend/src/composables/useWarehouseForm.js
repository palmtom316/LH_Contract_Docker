import { computed, onMounted, ref, watch } from "vue";
import { useRoute } from "vue-router";
import {
	getAvailableStock,
	getLocation,
	getMyWarehouseScopes,
	listLocations,
	listMaterials,
	listProjects,
} from "@/api/warehouse";
import { useUserStore } from "@/stores/user";
import { todayISODate } from "@/utils/dateInput";

export function useWarehouseForm() {
	const userStore = useUserStore();
	const route = useRoute();
	const warehouses = ref([]);
	const locations = ref([]);
	const projects = ref([]);
	const materials = ref([]);
	const available = ref(null);
	const submitting = ref(false);

	const form = ref({
		warehouse_id: null,
		location_id: null,
		project_id: null,
		material_id: null,
		quantity: "",
		occurred_on: todayISODate(),
		handler: userStore.user?.full_name || userStore.user?.username || "",
		business_type: "PURCHASE",
		reference_no: "",
		description: "",
		delivery_note_file: "",
		delivery_note_file_name: "",
		scrap_basis_file: "",
		scrap_basis_file_name: "",
		source_warehouse_id: null,
		source_location_id: null,
		source_project_id: null,
		target_warehouse_id: null,
		target_location_id: null,
		target_project_id: null,
		supplier_name: "",
		purchase_order_no: "",
		delivery_note_no: "",
		acceptance_no: "",
		acceptor: "",
		qc_result: "",
		manufacturer: "",
		batch_no: "",
		requisition_no: "",
		work_package: "",
		crew_name: "",
		requester_name: "",
		receiver_name: "",
		signed_off: false,
	});

	const selectedWarehouse = computed(() =>
		warehouses.value.find((item) => item.id === form.value.warehouse_id),
	);

	async function applyLocation(locationId) {
		if (!locationId) return;
		const location = await getLocation(locationId);
		const rows = await listLocations(location.warehouse_id);
		locations.value = rows;
		form.value.warehouse_id = location.warehouse_id;
		form.value.source_warehouse_id = location.warehouse_id;
		form.value.location_id = location.id;
		form.value.source_location_id = location.id;
	}

	async function loadLookups() {
		warehouses.value = await getMyWarehouseScopes();
		projects.value = await listProjects();
		const queryLocation = Number(route.query.location_id || 0);
		if (queryLocation) {
			await applyLocation(queryLocation);
		} else {
			const defaultWarehouse =
				warehouses.value.find((item) => item.is_default) || warehouses.value[0];
			if (defaultWarehouse) {
				form.value.warehouse_id =
					defaultWarehouse.warehouse_id || defaultWarehouse.id;
				form.value.source_warehouse_id = form.value.warehouse_id;
			}
		}
		if (route.params.id) {
			form.value.material_id = Number(route.params.id);
		}
	}

	async function refreshLocations(warehouseId, target = "location_id") {
		if (!warehouseId) {
			locations.value = [];
			return;
		}
		const rows = await listLocations(warehouseId);
		locations.value = rows;
		const current = form.value[target];
		if (current && rows.some((item) => item.id === current)) return;
		const fallback = rows.find((item) => item.is_default) || rows[0];
		if (fallback) form.value[target] = fallback.id;
	}

	async function searchMaterials(q) {
		if (!q) return;
		materials.value = await listMaterials({ q });
	}

	async function refreshAvailable() {
		const { warehouse_id, location_id, project_id, material_id } = form.value;
		if (!warehouse_id || !location_id || !project_id || !material_id) {
			available.value = null;
			return;
		}
		const res = await getAvailableStock({
			warehouse_id,
			location_id,
			project_id,
			material_id,
		});
		available.value = res.quantity;
	}

	watch(
		() => form.value.warehouse_id,
		(id) => refreshLocations(id, "location_id"),
	);
	watch(
		() => [
			form.value.warehouse_id,
			form.value.location_id,
			form.value.project_id,
			form.value.material_id,
		],
		refreshAvailable,
	);

	onMounted(loadLookups);

	return {
		form,
		warehouses,
		locations,
		projects,
		materials,
		available,
		submitting,
		selectedWarehouse,
		searchMaterials,
		refreshLocations,
		refreshAvailable,
		applyLocation,
	};
}
