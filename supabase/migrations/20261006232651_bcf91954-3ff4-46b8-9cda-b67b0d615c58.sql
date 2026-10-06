CREATE OR REPLACE FUNCTION public.admin_list_projects()
RETURNS TABLE (project_id uuid, owner_id uuid, client_type text, stage text, created_at timestamptz, updated_at timestamptz, ca_linked boolean)
LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path TO 'public' AS $$
BEGIN
  IF auth.uid() IS NULL THEN RAISE EXCEPTION 'non authentifié'; END IF;
  IF NOT public.has_permission(auth.uid(), 'projects.read_meta') THEN
    PERFORM public.log_admin_action('projects.list_meta','projects.read_meta',NULL,NULL,
      CASE WHEN public.is_suspended(auth.uid()) THEN 'compte suspendu' ELSE 'permission manquante' END,'denied');
    RETURN;
  END IF;
  PERFORM public.log_admin_action('projects.list_meta','projects.read_meta',NULL,NULL,NULL,'allowed');
  RETURN QUERY
    SELECT p.id, p.user_id, p.client_type, p.stage::text, p.created_at, p.updated_at, p.ca_project_id IS NOT NULL
    FROM public.projects p
    ORDER BY p.updated_at DESC
    LIMIT 500;
END; $$;
REVOKE ALL ON FUNCTION public.admin_list_projects() FROM PUBLIC, anon;
GRANT EXECUTE ON FUNCTION public.admin_list_projects() TO authenticated;