DROP POLICY IF EXISTS "matrix readable" ON public.role_permissions;
REVOKE ALL ON public.role_permissions FROM anon, authenticated;
GRANT ALL ON public.role_permissions TO service_role;
ALTER TABLE public.role_permissions ENABLE ROW LEVEL SECURITY;