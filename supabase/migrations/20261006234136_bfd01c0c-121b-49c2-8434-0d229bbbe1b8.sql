CREATE OR REPLACE FUNCTION public.admin_list_gate_projects()
RETURNS TABLE (project_id uuid, owner_id uuid, stage text, ca_project_id text)
LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path TO 'public' AS $$
BEGIN
  IF auth.uid() IS NULL THEN RAISE EXCEPTION 'non authentifié'; END IF;
  IF NOT public.has_permission(auth.uid(), 'gates.read') THEN
    PERFORM public.log_admin_action('gates.list','gates.read',NULL,NULL,
      CASE WHEN public.is_suspended(auth.uid()) THEN 'compte suspendu' ELSE 'permission manquante' END,'denied');
    RETURN;
  END IF;
  PERFORM public.log_admin_action('gates.list','gates.read',NULL,NULL,NULL,'allowed');
  RETURN QUERY
    SELECT p.id, p.user_id, p.stage::text, p.ca_project_id
    FROM public.projects p
    WHERE p.ca_project_id IS NOT NULL
    ORDER BY p.updated_at DESC
    LIMIT 100;
END; $$;
REVOKE ALL ON FUNCTION public.admin_list_gate_projects() FROM PUBLIC, anon;
GRANT EXECUTE ON FUNCTION public.admin_list_gate_projects() TO authenticated;